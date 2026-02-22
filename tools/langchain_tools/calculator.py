"""
Calculator Tool for Vishleshak AI v1
Performs mathematical calculations
"""

import math
import logging
from typing import Any, Union
from tools.tool_registry import BaseTool
from config import tool_config

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """
    Perform mathematical calculations
    
    Features:
    - Basic arithmetic
    - Advanced math functions
    - Safe evaluation
    - Precision control
    
    Usage:
        tool = CalculatorTool()
        result = tool.run("(500 * 0.142) - (500 * 0.10)")
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description=(
                "Perform mathematical calculations and expressions. "
                "Supports basic arithmetic (+, -, *, /), exponents (**, ^), "
                "parentheses, and math functions (sqrt, sin, cos, log, etc.). "
                "Input should be a valid mathematical expression. "
                "Example: '(500 * 0.142) - (500 * 0.10)'"
            ),
            category="langchain"
        )
        self.precision = tool_config.CALCULATOR_PRECISION
    
    def run(self, expression: str) -> Union[float, str]:
        """
        Evaluate mathematical expression
        
        Args:
            expression: Mathematical expression as string
            
        Returns:
            Calculated result or error message
        """
        if not tool_config.ENABLE_CALCULATOR:
            return "Calculator is disabled"
        
        try:
            # Clean expression
            expression = expression.strip()
            
            # Replace common patterns
            expression = expression.replace("^", "**")
            expression = expression.replace("×", "*")
            expression = expression.replace("÷", "/")
            
            # Safe evaluation with math functions
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "pi": math.pi,
                "e": math.e,
            }
            
            # Evaluate
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            # Round to precision
            if isinstance(result, float):
                result = round(result, self.precision)
            
            return result
        
        except Exception as e:
            error_msg = f"Calculation error: {str(e)}"
            logger.error(error_msg)
            return error_msg
