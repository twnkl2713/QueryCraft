import re
import logging
from typing import Tuple, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from app.utils.config import settings

logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self, schema_manager):
        self.schema_manager = schema_manager
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
            self.model = AutoModelForCausalLM.from_pretrained(settings.MODEL_NAME)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            logger.warning(f"Could not load model {settings.MODEL_NAME}: {e}")
            self.model = None
        
        # Safety patterns
        self.dangerous_patterns = [
            r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|EXEC)\b',
            r';.*;',  # Multiple statements
            r'--',   # SQL comments
            r'/\*.*\*/'  # Block comments
        ]
    
    def create_enhanced_prompt(self, natural_language_query: str) -> str:
        schema_context = self.schema_manager.get_schema_context()
        
        prompt = f"""
You are an expert SQL query generator. Convert natural language questions to SQL queries.

SCHEMA INFORMATION:
{schema_context}

IMPORTANT RULES:
1. Generate ONLY the SQL query, no explanations
2. Use WHERE clauses for filtering
3. Use appropriate aggregate functions (COUNT, SUM, AVG, MAX, MIN)
4. Always use table aliases for better readability
5. Include ORDER BY when sorting is implied
6. Use LIMIT for "top N" queries

EXAMPLES:
- "Show me all employees in Engineering" → "SELECT * FROM employees WHERE department = 'Engineering';"
- "Count the number of high earners" → "SELECT COUNT(*) FROM employees WHERE salary > 100000;"
- "Top 5 highest paid employees" → "SELECT * FROM employees ORDER BY salary DESC LIMIT 5;"
- "Average salary by department" → "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department;"

QUESTION: {natural_language_query}

SQL QUERY:
"""
        return prompt
    
    def generate_sql(self, natural_language_query: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate SQL query with safety checks"""
        try:
            # If model is not available, use rule-based approach
            if self.model is None:
                return self._rule_based_sql(natural_language_query), None
            
            prompt = self.create_enhanced_prompt(natural_language_query)
            
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=len(inputs[0]) + settings.MAX_SQL_LENGTH,
                    num_return_sequences=1,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            sql_query = self._extract_sql(generated_text)
            
            # Safety validation
            is_safe, safety_message = self._validate_sql_safety(sql_query)
            if not is_safe:
                return None, f"Safety violation: {safety_message}"
            
            return sql_query, None
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            # Fallback to rule-based
            return self._rule_based_sql(natural_language_query), None
    
    def _rule_based_sql(self, query: str) -> str:
        """Rule-based SQL generation as fallback"""
        query_lower = query.lower()
        
        if "count" in query_lower and "department" in query_lower:
            return "SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department;"
        elif "average" in query_lower and "salary" in query_lower:
            if "department" in query_lower:
                return "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department;"
            else:
                return "SELECT AVG(salary) as average_salary FROM employees;"
        elif "highest" in query_lower or "top" in query_lower:
            return "SELECT * FROM employees ORDER BY salary DESC LIMIT 5;"
        elif "lowest" in query_lower:
            return "SELECT * FROM employees ORDER BY salary ASC LIMIT 5;"
        elif "department" in query_lower:
            dept = self._extract_department(query_lower)
            if dept:
                return f"SELECT * FROM employees WHERE department = '{dept}';"
            else:
                return "SELECT DISTINCT department FROM employees;"
        elif "city" in query_lower or "location" in query_lower:
            return "SELECT DISTINCT residence_city FROM employees LIMIT 10;"
        else:
            return "SELECT * FROM employees LIMIT 10;"
    
    def _extract_department(self, query: str) -> str:
        """Extract department name from query"""
        departments = ['it', 'marketing', 'sales', 'finance', 'hr']
        for dept in departments:
            if dept in query:
                return dept.title()
        return ""
    
    def _extract_sql(self, generated_text: str) -> str:
        """Extract SQL query from generated text"""
        sql_markers = ["SQL QUERY:", "SELECT", "WITH"]
        for marker in sql_markers:
            if marker in generated_text:
                if marker == "SQL QUERY:":
                    sql_part = generated_text.split("SQL QUERY:")[-1].strip()
                else:
                    sql_part = generated_text[generated_text.find(marker):]
                
                # Clean up the SQL
                sql_part = re.split(r'[;\n]', sql_part)[0].strip()
                return sql_part + ";" if not sql_part.endswith(";") else sql_part
        
        return "SELECT * FROM employees LIMIT 10;"
    
    def _validate_sql_safety(self, sql_query: str) -> Tuple[bool, str]:
        """Validate SQL query for safety"""
        if not settings.ENABLE_SAFETY_CHECKS:
            return True, "Safety checks disabled"
        
        sql_upper = sql_query.upper()
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, f"Dangerous SQL pattern detected: {pattern}"
        
        return True, "Query is safe"