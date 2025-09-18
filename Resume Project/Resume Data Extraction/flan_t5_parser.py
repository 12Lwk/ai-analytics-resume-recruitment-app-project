from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import json
import re
import os
import fitz  # PyMuPDF
import pandas as pd
from typing import Dict, List
import time
from tqdm import tqdm

class FlanT5ResumeParser:
    def __init__(self):
        model_name = "google/flan-t5-base"
        print(f"🤖 Loading {model_name}...")
        
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.output_dir = "parsed_data"
        os.makedirs(self.output_dir, exist_ok=True)
        print("✅ Model loaded successfully!")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"❌ Error extracting text from {pdf_path}: {e}")
            return ""
    
    def parse_resume_with_flan(self, resume_text: str, filename: str = "") -> Dict:
        """Parse resume with visual progress"""
        if filename:
            print(f"🔍 Analyzing: {filename}")
        
        # Use structured prompts for better results
        return {
            "summary": self._generate_summary(resume_text),
            "skills": self._extract_skills(resume_text),
            "experience": self._extract_experience(resume_text),
            "education": self._extract_education(resume_text),
            "affiliations": []
        }
    
    def _generate_text(self, prompt: str, max_length: int = 100) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=2,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def _generate_summary(self, text: str) -> str:
        prompt = f"Summarize this person's professional background: {text[:800]}"
        return self._generate_text(prompt, max_length=80)
    
    def _extract_skills(self, text: str) -> List[str]:
        prompt = f"List the technical skills from this resume: {text[:1000]}"
        skills_text = self._generate_text(prompt, max_length=100)
        skills = [s.strip() for s in skills_text.split(',') if s.strip()]
        return skills[:10]
    
    def _extract_experience(self, text: str) -> List[Dict]:
        prompt = f"Extract job titles and companies from this resume: {text[:1200]}"
        exp_text = self._generate_text(prompt, max_length=150)
        
        experiences = []
        lines = exp_text.split('\n')
        for line in lines[:3]:
            if line.strip():
                experiences.append({
                    "job_title": line.strip(),
                    "company_name": "",
                    "dates": "",
                    "description": ""
                })
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict]:
        prompt = f"Extract education details from this resume: {text[:1000]}"
        edu_text = self._generate_text(prompt, max_length=100)
        
        education = []
        if edu_text.strip():
            education.append({
                "degree": edu_text.strip(),
                "university": "",
                "year": ""
            })
        return education
    
    def process_directory(self, resume_dir: str) -> List[Dict]:
        """Process all PDF files with visual progress"""
        all_resumes = []
        
        print(f"📂 Scanning directory: {resume_dir}")
        
        if not os.path.exists(resume_dir):
            print(f"❌ Directory does not exist: {resume_dir}")
            return all_resumes
        
        # Find all PDF files
        pdf_files = []
        print("🔍 Finding PDF files...")
        
        for item in os.listdir(resume_dir):
            item_path = os.path.join(resume_dir, item)
            
            if os.path.isdir(item_path):
                category = item.upper()
                print(f"📁 Checking folder: {category}")
                
                for file in os.listdir(item_path):
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(item_path, file)
                        pdf_files.append((file_path, category))
        
        print(f"📄 Found {len(pdf_files)} PDF files to process")
        
        if len(pdf_files) == 0:
            print("❌ No PDF files found!")
            return all_resumes
        
        # Process each PDF with progress
        for i, (pdf_path, category) in enumerate(pdf_files, 1):
            filename = os.path.basename(pdf_path)
            print(f"\n[{i}/{len(pdf_files)}] Processing: {filename}")
            
            try:
                # Extract text
                resume_text = self.extract_text_from_pdf(pdf_path)
                
                if not resume_text:
                    print(f"⚠️ No text extracted from {filename}")
                    continue
                
                print(f"📝 Extracted {len(resume_text)} characters")
                
                # Parse with FLAN-T5
                parsed_resume = self.parse_resume_with_flan(resume_text, filename)
                
                if parsed_resume:
                    parsed_resume["filename"] = filename
                    parsed_resume["category"] = category
                    all_resumes.append(parsed_resume)
                    print(f"✅ Successfully parsed {filename}")
                    print(f"   Summary: {parsed_resume['summary'][:100]}...")
                
                time.sleep(1)  # Small delay
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                continue
        
        return all_resumes
    
    def save_results(self, parsed_resumes: List[Dict]):
        """Save results to JSON and CSV"""
        print("\n💾 Saving results...")
        
        # Save JSON
        json_path = os.path.join(self.output_dir, "flan_t5_parsed_resumes.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed_resumes, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved: {json_path}")
        
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
                'education_count': len(resume['education'])
            }
            
            if resume['experience']:
                first_job = resume['experience'][0]
                row['first_job_title'] = first_job.get('job_title', '')
            
            if resume['education']:
                first_edu = resume['education'][0]
                row['degree'] = first_edu.get('degree', '')
            
            df_rows.append(row)
        
        # Save CSV
        df = pd.DataFrame(df_rows)
        csv_path = os.path.join(self.output_dir, "flan_t5_parsed_resumes.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"📊 CSV saved: {csv_path}")
        
        return df

# Main execution
if __name__ == "__main__":
    RESUME_DIR = r"C:\Users\User\OneDrive - Asia Pacific University\Side Project\Resume Project\Resume Dataset\pdf data"
    
    print("🚀 === FLAN-T5 RESUME PARSER ===")
    
    try:
        # Initialize parser
        parser = FlanT5ResumeParser()
        
        # Process all resumes
        parsed_resumes = parser.process_directory(RESUME_DIR)
        
        if parsed_resumes:
            # Save results
            df = parser.save_results(parsed_resumes)
            
            # Display summary
            print(f"\n📊 === SUMMARY ===")
            print(f"✅ Total resumes processed: {len(parsed_resumes)}")
            print(f"📁 Categories: {df['category'].value_counts().to_dict()}")
            print(f"🛠️ Average skills per resume: {df['skills_count'].mean():.1f}")
            print(f"💼 Average experience entries: {df['experience_count'].mean():.1f}")
            
        else:
            print("❌ No resumes were successfully processed!")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

