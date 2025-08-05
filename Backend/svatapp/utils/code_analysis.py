import re
from langchain_community.llms import Ollama
import requests
from typing import List, Tuple, Dict, Any

def analyze_code_with_llm(code: str, model_name: str, temperature: float = 0.7) -> str:
    """
    Analyze the provided code for vulnerabilities using the specified LLM model.
    
    Args:
        code (str): The code to analyze
        model_name (str): The name of the LLM model to use
        temperature (float): The temperature setting for the LLM
    
    Returns:
        str: The analysis result from the LLM
    """
    try:
        llm = Ollama(model=model_name, temperature=temperature, num_ctx=4096, num_predict=2048)
        prompt = f"""You are a security expert. Analyze the following code for potential security vulnerabilities.
Identify any CVE or CWE vulnerabilities, provide a description, and suggest fixes.
Code:
{code}
Output format:
- Vulnerability: [Name]
- CVE ID: [CVE-XXXX-XXXX]
- CWE ID: [CWE-XXX]
- Description: [Description]
- Recommended Fix: [Fix]
"""
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        raise Exception(f"Error analyzing code with LLM: {str(e)}")

def extract_ids_from_response(response: str) -> Tuple[List[str], List[str]]:
    """
    Extract CVE and CWE IDs from the LLM response.
    
    Args:
        response (str): The response text from the LLM
    
    Returns:
        Tuple[List[str], List[str]]: Lists of CVE and CWE IDs
    """
    cve_ids = re.findall(r'CVE-\d{4}-\d{4,7}', response, re.IGNORECASE)
    cwe_ids = re.findall(r'CWE-\d+', response, re.IGNORECASE)
    return cve_ids, cwe_ids

def fetch_cve_details(cve_id: str) -> Dict[str, Any]:
    """
    Fetch details for a given CVE ID from the NVD API.
    
    Args:
        cve_id (str): The CVE ID to query
    
    Returns:
        Dict[str, Any]: Details about the CVE
    """
    try:
        url = f"https://services.nvd.nist.gov/rest/json/cve/1.0/{cve_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cve = data.get('result', {}).get('CVE_Items', [{}])[0]
            description = cve.get('cve', {}).get('description', {}).get('description_data', [{}])[0].get('value', 'No description available')
            cvss_score = cve.get('impact', {}).get('baseMetricV3', {}).get('cvssV3', {}).get('baseScore', 'N/A')
            return {
                "description": description,
                "cvss_score": cvss_score
            }
        return {"description": "No description available", "cvss_score": "N/A"}
    except Exception as e:
        return {"description": f"Error fetching CVE details: {str(e)}", "cvss_score": "N/A"}

def fetch_cwe_details(cwe_id: str) -> Dict[str, Any]:
    """
    Fetch details for a given CWE ID from the MITRE CWE database.
    
    Args:
        cwe_id (str): The CWE ID to query
    
    Returns:
        Dict[str, Any]: Details about the CWE
    """
    try:
        cwe_number = cwe_id.replace("CWE-", "")
        url = f"https://cwe.mitre.org/data/definitions/{cwe_number}.html"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Note: Parsing HTML is simplified here; in production, use BeautifulSoup or similar
            title_match = re.search(r'<h2>(.*?)</h2>', response.text)
            title = title_match.group(1) if title_match else cwe_id
            description_match = re.search(r'<div id="Description">.*?<p>(.*?)</p>', response.text, re.DOTALL)
            description = description_match.group(1).strip() if description_match else "No description available"
            return {
                "title": title,
                "description": description
            }
        return {"title": cwe_id, "description": "No description available"}
    except Exception as e:
        return {"title": cwe_id, "description": f"Error fetching CWE details: {str(e)}"}