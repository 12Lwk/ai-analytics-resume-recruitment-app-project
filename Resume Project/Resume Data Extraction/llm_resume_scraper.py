import fitz
import json
import os
import requests
import pandas as pd
from typing import Dict, List
import time

class LLMResumeParser:
    def __init__(self, model_name="gemma3:latest"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self.output_dir = "parsed_data"
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def parse_resume_with_llm(self, resume_text: str) -> Dict:
        """Use LLM to parse resume into structured format"""
        
        prompt = f"""
        You are an expert resume parser. Parse the following resume text and extract information into this exact JSON structure. 
        Be precise and only extract what's clearly stated. If information is not available, use empty string or empty array.

        IMPORTANT RULES:
        - For skills: Only extract technical skills, software, programming languages, certifications, tools
        - For experience: Clearly separate job titles from company names
        - For education: Extract degree, major, university, and graduation year
        - Return ONLY valid JSON, no additional text

        Required JSON structure:
        {{
            "summary": "Brief professional summary or objective statement",
            "skills": ["skill1", "skill2", "skill3"],
            "experience": [
                {{
                    "job_title": "Exact Job Title",
                    "company_name": "Company Name Only",
                    "dates": "Start Date - End Date or Duration",
                    "location": "City, State",
                    "responsibilities": ["responsibility1", "responsibility2"]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree Type and Field",
                    "major": "Major/Field of Study",
                    "university": "University/Institution Name",
                    "year": "Graduation Year",
                    "location": "City, State"
                }}
            ],
            "affiliations": ["professional affiliation1", "certification1"]
        }}

        Resume Text:
        {resume_text[:4000]}

        JSON Response:
        """
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        try:
            print("Sending request to Ollama...")
            response = requests.post(self.ollama_url, json=payload, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['response'].strip()
                
                # Try to extract JSON from response
                try:
                    # Find JSON in response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = response_text[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        print("No JSON found in response")
                        return self._get_empty_structure()
                        
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Response: {response_text[:500]}...")
                    return self._get_empty_structure()
            else:
                print(f"HTTP Error: {response.status_code}")
                return self._get_empty_structure()
                
        except requests.exceptions.Timeout:
            print("Request timeout - Ollama might be slow")
            return self._get_empty_structure()
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._get_empty_structure()
    
    def _get_empty_structure(self):
        """Return empty structure if parsing fails"""
        return {
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "affiliations": []
        }
    
    def get_category_from_filename(self, filename: str) -> str:
        """Extract category from filename or directory structure"""
        # You can modify this based on your file organization
        filename_upper = filename.upper()
        
        if "ACCOUNTANT" in filename_upper:
            return "ACCOUNTANT"
        elif "ENGINEER" in filename_upper:
            return "ENGINEER"
        elif "MANAGER" in filename_upper:
            return "MANAGER"
        # Add more categories as needed
        else:
            return "UNKNOWN"
    
    def process_resume_file(self, pdf_path: str) -> Dict:
        """Process a single resume file"""
        filename = os.path.basename(pdf_path)
        print(f"\nProcessing: {filename}")
        
        # Extract text
        resume_text = self.extract_text_from_pdf(pdf_path)
        
        if not resume_text:
            print(f"No text extracted from {filename}")
            return None
        
        print(f"Extracted {len(resume_text)} characters")
        
        # Parse with LLM
        parsed_data = self.parse_resume_with_llm(resume_text)
        
        # Add metadata
        parsed_data["filename"] = filename
        parsed_data["category"] = self.get_category_from_filename(filename)
        
        return parsed_data
    
    def process_directory(self, resume_dir: str) -> List[Dict]:
        """Process all PDF files in directory and subdirectories"""
        all_resumes = []
        
        # Check if directory exists
        if not os.path.exists(resume_dir):
            print(f"❌ Directory does not exist: {resume_dir}")
            return all_resumes
        
        print(f"📁 Scanning directory: {resume_dir}")
        
        # Look for PDFs in subdirectories (category folders)
        pdf_files = []
        
        try:
            items = os.listdir(resume_dir)
            print(f"Found {len(items)} items in directory")
            
            for item in items:
                item_path = os.path.join(resume_dir, item)
                
                if os.path.isdir(item_path):
                    category = item.upper()
                    print(f"📂 Checking category folder: {category}")
                    
                    try:
                        files_in_category = os.listdir(item_path)
                        pdf_count = 0
                        
                        for file in files_in_category:
                            if file.lower().endswith('.pdf'):
                                file_path = os.path.join(item_path, file)
                                pdf_files.append((file_path, category))
                                pdf_count += 1
                        
                        print(f"   Found {pdf_count} PDF files in {category}")
                        
                    except Exception as e:
                        print(f"   ❌ Error reading {category}: {e}")
        
        except Exception as e:
            print(f"❌ Error reading main directory: {e}")
            return all_resumes
        
        total_files = len(pdf_files)
        print(f"\n🎯 Total PDF files found: {total_files}")
        
        if total_files == 0:
            print("❌ No PDF files found! Check your directory structure.")
            return all_resumes
        
        # Process files
        for i, (pdf_path, category) in enumerate(pdf_files, 1):
            filename = os.path.basename(pdf_path)
            print(f"\n[{i}/{total_files}] Processing: {filename} (Category: {category})")
            
            try:
                parsed_resume = self.process_resume_file(pdf_path)
                if parsed_resume:
                    parsed_resume["category"] = category
                    all_resumes.append(parsed_resume)
                    print(f"✅ Successfully parsed {filename}")
                else:
                    print(f"❌ Failed to parse {filename}")
                
                # Small delay to avoid overwhelming Ollama
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                continue
        
        return all_resumes
    
    def save_results(self, parsed_resumes: List[Dict]):
        """Save results in both JSON and CSV formats"""
        
        # Save JSON
        json_path = os.path.join(self.output_dir, "llm_parsed_resumes.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_resumes, f, indent=2, ensure_ascii=False)
        
        # Convert to DataFrame for CSV
        df_rows = []
        for resume in parsed_resumes:
            row = {
                'filename': resume['filename'],
                'category': resume['category'],
                'summary': resume['summary'],
                'skills_count': len(resume['skills']),
                'skills': ' | '.join(resume['skills']),
                'experience_count': len(resume['experience']),
                'education_count': len(resume['education']),
                'affiliations': ' | '.join(resume['affiliations'])
            }
            
            # Add first job details
            if resume['experience']:
                first_job = resume['experience'][0]
                row['first_job_title'] = first_job.get('job_title', '')
                row['first_company'] = first_job.get('company_name', '')
                row['first_job_dates'] = first_job.get('dates', '')
            
            # Add education details
            if resume['education']:
                first_edu = resume['education'][0]
                row['degree'] = first_edu.get('degree', '')
                row['university'] = first_edu.get('university', '')
                row['graduation_year'] = first_edu.get('year', '')
            
            df_rows.append(row)
        
        # Save CSV
        df = pd.DataFrame(df_rows)
        csv_path = os.path.join(self.output_dir, "llm_parsed_resumes.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"\n✓ Results saved:")
        print(f"  JSON: {json_path}")
        print(f"  CSV: {csv_path}")
        
        return df

# Main execution
if __name__ == "__main__":
    # Configuration
    RESUME_DIR = r"C:\Users\User\OneDrive - Asia Pacific University\Side Project\Resume Project\Resume Dataset\pdf data"
    
    # Optional: Test with specific categories only
    TEST_CATEGORIES = ["ACCOUNTANT", "ENGINEER", "HR"]  # Remove this line to process all
    
    print("=== LLM-Powered Resume Parser ===")
    print("Make sure Ollama is running: ollama serve")
    
    # Initialize parser
    parser = LLMResumeParser()
    
    # Process all resumes
    print(f"\nStarting to process resumes from: {RESUME_DIR}")
    parsed_resumes = parser.process_directory(RESUME_DIR)
    
    if parsed_resumes:
        # Save results
        df = parser.save_results(parsed_resumes)
        
        # Display summary
        print(f"\n=== SUMMARY ===")
        print(f"Total resumes processed: {len(parsed_resumes)}")
        print(f"Categories found: {df['category'].value_counts().to_dict()}")
        print(f"Average skills per resume: {df['skills_count'].mean():.1f}")
        print(f"Average experience entries: {df['experience_count'].mean():.1f}")
        
    else:
        print("No resumes were successfully processed!")


