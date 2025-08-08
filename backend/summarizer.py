import httpx
import json
from typing import Dict, Any, Optional
from config import settings


class CodeSummarizer:
    def __init__(self):
        self.llm_provider = settings.llm_provider
        self.llm_model = settings.llm_model
        self.ollama_host = settings.ollama_host
    
    async def summarize_code(self, code: str, language: str, chunk_type: str, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary for a code chunk using self-hosted LLM."""
        if self.llm_provider == "ollama":
            return await self._summarize_with_ollama(code, language, chunk_type, function_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    async def _summarize_with_ollama(self, code: str, language: str, chunk_type: str, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate summary using Ollama."""
        prompt = self._create_summary_prompt(code, language, chunk_type, function_name)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.llm_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "num_predict": 200
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    summary = result.get("response", "").strip()
                    
                    # Clean up the summary
                    summary = self._clean_summary(summary)
                    
                    # Create combined text (summary + code)
                    combined = self._create_combined_text(summary, code)
                    
                    # Estimate token count (rough approximation)
                    tokens = len(code.split()) + len(summary.split())
                    
                    return {
                        "summary": summary,
                        "combined": combined,
                        "tokens": tokens,
                        "model": self.llm_model
                    }
                else:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            # Fallback: create a simple summary
            fallback_summary = f"# {chunk_type.title()}"
            if function_name:
                fallback_summary += f" {function_name}"
            fallback_summary += f" in {language}"
            
            combined = self._create_combined_text(fallback_summary, code)
            tokens = len(code.split()) + len(fallback_summary.split())
            
            return {
                "summary": fallback_summary,
                "combined": combined,
                "tokens": tokens,
                "model": "fallback",
                "error": str(e)
            }
    
    def _create_summary_prompt(self, code: str, language: str, chunk_type: str, function_name: Optional[str] = None) -> str:
        """Create a prompt for code summarization."""
        name_part = f" named '{function_name}'" if function_name else ""
        
        prompt = f"""You are a code analysis expert. Please provide a concise summary of the following {language} {chunk_type}{name_part}.

Code:
```{language}
{code}
```

Please provide a clear, concise summary that explains:
1. What this code does
2. Its main purpose or functionality
3. Any important details about inputs, outputs, or behavior

Format your response as a brief comment starting with "# " followed by your summary.

Summary:"""
        
        return prompt
    
    def _clean_summary(self, summary: str) -> str:
        """Clean up the LLM-generated summary."""
        # Remove any markdown formatting
        summary = summary.replace("```", "").replace("`", "")
        
        # Ensure it starts with "# "
        if not summary.startswith("#"):
            summary = "# " + summary
        
        # Remove any trailing whitespace or newlines
        summary = summary.strip()
        
        return summary
    
    def _create_combined_text(self, summary: str, code: str) -> str:
        """Combine summary and code into a single text for embedding."""
        return f"{summary}\n\n{code}"
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_host}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False


# Global summarizer instance
summarizer = CodeSummarizer()
