import os
import fitz  # PyMuPDF for PDF text extraction
import re
import json

# --- Configuration ---
RESUME_DATASET_DIR = r"C:\Users\User\OneDrive - Asia Pacific University\Side Project\Resume Project\Resume Dataset\pdf data" # Assuming this is in the same directory as your script
OUTPUT_DIR = "parsed_data"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- PDF Text Extraction Function ---
def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF file."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

# --- Parsing Functions (Generalized for common resume sections) ---

def parse_summary(text):
    """Extracts the summary section."""
    summary = ""
    
    # Look for Summary section that ends before Skills/Experience/Highlights
    patterns = [
        r"Summary\s*:?\s*(.*?)\s*(?:Skills|Experience|Highlights|Education)",
        r"Professional Summary\s*:?\s*(.*?)\s*(?:Skills|Experience|Highlights|Education)",
        r"Objective\s*:?\s*(.*?)\s*(?:Skills|Experience|Highlights|Education)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            summary = match.group(1).strip()
            break
    
    # Clean up: remove bullet points, extra whitespace, and HTML tags
    summary = re.sub(r'<[^>]*>', '', summary)
    summary = re.sub(r'^\s*[•·-]\s*', '', summary, flags=re.MULTILINE)
    summary = re.sub(r'\s+', ' ', summary).strip()
    
    return summary

def parse_skills(text):
    """Extracts only actual skills, not experience details."""
    skills = []
    
    # Look for dedicated Skills section
    skills_patterns = [
        r"Skills\s*:?\s*(.*?)\s*(?:Experience|Education|Professional|Highlights|\n\n)",
        r"Technical Skills\s*:?\s*(.*?)\s*(?:Experience|Education|Professional|\n\n)",
        r"Core Competencies\s*:?\s*(.*?)\s*(?:Experience|Education|Professional|\n\n)"
    ]
    
    for pattern in skills_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            skills_text = match.group(1).strip()
            
            # Clean and split skills
            skills_text = re.sub(r'<[^>]*>', '', skills_text)
            
            # Split by common delimiters
            skill_items = re.split(r'[,;•·\n]', skills_text)
            
            for skill in skill_items:
                skill = skill.strip()
                # Filter out non-skills (dates, company names, long sentences)
                if (len(skill) > 2 and len(skill) < 50 and 
                    not re.search(r'\d{2,4}', skill) and  # No years
                    not re.search(r'Company|Inc\.|Corp\.|LLC', skill, re.IGNORECASE) and
                    not skill.lower().startswith(('responsible', 'managed', 'developed', 'led'))):
                    skills.append(skill)
            break
    
    return list(set(skills))  # Remove duplicates

def parse_experience(text):
    """Extracts job experience entries with proper company/title separation."""
    experiences = []
    
    # Find Experience section
    exp_match = re.search(r"Experience\s*:?\s*(.*?)(?=\n\s*Education|\n\s*Skills|\Z)", 
                         text, re.DOTALL | re.IGNORECASE)
    
    if not exp_match:
        return experiences
    
    exp_text = exp_match.group(1)
    
    # Split by date patterns to identify job entries
    date_patterns = [
        r'(\d{1,2}/\d{4}\s+to\s+(?:Current|\d{1,2}/\d{4}))',
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s+to\s+(?:Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}))'
    ]
    
    # Find all job blocks
    job_blocks = []
    for pattern in date_patterns:
        matches = list(re.finditer(pattern, exp_text, re.IGNORECASE))
        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(exp_text)
                job_block = exp_text[start:end].strip()
                job_blocks.append(job_block)
            break
    
    for block in job_blocks:
        # Extract date
        date_match = re.search(r'(\d{1,2}/\d{4}\s+to\s+(?:Current|\d{1,2}/\d{4})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s+to\s+(?:Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}))', 
                              block, re.IGNORECASE)
        
        if date_match:
            dates = date_match.group(1)
            
            # Extract the line after dates (usually contains title and company)
            after_date = block[date_match.end():].strip()
            lines = [line.strip() for line in after_date.split('\n') if line.strip()]
            
            if lines:
                # First line usually contains job title and company
                title_company_line = lines[0]
                
                # Try to separate title and company
                # Common patterns: "Title - Company" or "Title Company"
                if ' - ' in title_company_line:
                    parts = title_company_line.split(' - ', 1)
                    job_title = parts[0].strip()
                    company_name = parts[1].strip()
                elif ' at ' in title_company_line:
                    parts = title_company_line.split(' at ', 1)
                    job_title = parts[0].strip()
                    company_name = parts[1].strip()
                else:
                    # Heuristic: assume first few words are title, rest is company
                    words = title_company_line.split()
                    if len(words) > 3:
                        job_title = ' '.join(words[:3])
                        company_name = ' '.join(words[3:])
                    else:
                        job_title = title_company_line
                        company_name = "Not specified"
                
                # Extract responsibilities (remaining lines)
                responsibilities = []
                for line in lines[1:]:
                    line = re.sub(r'^\s*[•·-]\s*', '', line)
                    if line and not re.search(r'\d{1,2}/\d{4}', line):
                        responsibilities.append(line)
                
                experience = {
                    "dates": dates,
                    "job_title": job_title,
                    "company_name": company_name,
                    "location": "",  # Extract if needed
                    "responsibilities": responsibilities[:5]  # Limit to 5
                }
                experiences.append(experience)
    
    return experiences


def parse_education(text):
    """Extracts education entries properly."""
    educations = []
    
    # Find Education section
    edu_match = re.search(r"Education\s*:?\s*(.*?)(?=\n\s*Skills|\n\s*Professional|\Z)", 
                         text, re.DOTALL | re.IGNORECASE)
    
    if not edu_match:
        return educations
    
    edu_text = edu_match.group(1)
    lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
    
    current_education = {}
    for line in lines:
        # Look for year patterns
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', line)
        
        if year_match:
            # Save previous education if exists
            if current_education:
                educations.append(current_education)
            
            year = year_match.group(1)
            
            # Extract degree and university
            # Common patterns: "Year Degree University" or "Degree Year University"
            line_clean = re.sub(r'<[^>]*>', '', line)
            
            # Try to identify degree keywords
            degree_keywords = ['B.S', 'B.A', 'M.S', 'M.A', 'MBA', 'Masters', 'Bachelor', 'Associate', 'Ph.D', 'Doctorate']
            degree = ""
            university = ""
            major = ""
            
            for keyword in degree_keywords:
                if keyword.lower() in line_clean.lower():
                    # Extract degree and surrounding text
                    degree_match = re.search(rf'({keyword}[^,\n]*)', line_clean, re.IGNORECASE)
                    if degree_match:
                        degree = degree_match.group(1).strip()
                        break
            
            # Extract university (usually contains "University", "College", "Institute")
            uni_match = re.search(r'([^,\n]*(?:University|College|Institute)[^,\n]*)', line_clean, re.IGNORECASE)
            if uni_match:
                university = uni_match.group(1).strip()
            
            current_education = {
                "year": year,
                "degree": degree,
                "major": major,
                "university": university,
                "location": ""
            }
    
    # Add last education
    if current_education:
        educations.append(current_education)
    
    return educations


def parse_affiliations(text):
    """Extracts affiliations."""
    affiliations = []
    aff_match = re.search(r"Professional Affiliations\s*(.*?)(?=\n\n|\Z)", text, re.DOTALL | re.IGNORECASE)
    if aff_match:
        raw_affs = aff_match.group(1).strip()
        # Split by lines and clean up source tags and bullet points
        clean_affs_str = re.sub(r'<[^>]*>', '', raw_affs)
        affiliations_list = [re.sub(r'^\s*•\s*|\s*•\s*$', '', line).strip() for line in clean_affs_str.split('\n') if line.strip()]
        # Filter out placeholder text
        affiliations = [aff for aff in affiliations_list if not aff.lower().startswith("enter any professional organizations")]
    return affiliations

# --- Main Processing Logic ---
def process_resumes_in_directory(root_dir):
    all_parsed_resumes = []

    for category_name in os.listdir(root_dir):
        category_path = os.path.join(root_dir, category_name)
        if os.path.isdir(category_path):
            print(f"Processing category: {category_name}")
            for filename in os.listdir(category_path):
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(category_path, filename)
                    print(f"  Extracting text from: {filename}")
                    resume_text = extract_text_from_pdf(pdf_path)

                    if resume_text:
                        parsed_resume = {
                            "filename": filename,
                            "category": category_name,
                            "summary": parse_summary(resume_text),
                            "skills": parse_skills(resume_text),
                            "experience": parse_experience(resume_text),
                            "education": parse_education(resume_text),
                            "affiliations": parse_affiliations(resume_text),
                            # You might want to include the raw_text for debugging, but remove for production
                            # "raw_text": resume_text 
                        }
                        all_parsed_resumes.append(parsed_resume)
                    else:
                        print(f"  Skipping {filename} due to empty content or extraction error.")
    return all_parsed_resumes

# --- Run the scraper ---
if __name__ == "__main__":
    print("Starting resume scraping process...")
    
    # Process all resumes
    parsed_data = process_resumes_in_directory(RESUME_DATASET_DIR)
    
    # Save the aggregated data
    output_filepath = os.path.join(OUTPUT_DIR, "all_parsed_resumes.json")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=4, ensure_ascii=False)
    
    print(f"\nScraping complete. Data saved to {output_filepath}")
    print(f"Total resumes processed: {len(parsed_data)}")

    # Optional: Print some sample data for verification
    if parsed_data:
        print("\n--- Sample Parsed Data (First 2 entries) ---")
        for i, entry in enumerate(parsed_data[:2]):
            print(f"\nResume {i+1} ({entry['filename']}):")
            print(f"  Category: {entry['category']}")
            print(f"  Summary: {entry['summary'][:150]}...") # Truncate for brevity
            print(f"  Skills ({len(entry['skills'])}): {entry['skills'][:5]}...") # First 5 skills
            print(f"  Experience ({len(entry['experience'])}):")
            for exp in entry['experience'][:2]: # First 2 experiences
                print(f"    - {exp.get('job_title', 'N/A')} at {exp.get('company_name', 'N/A')} ({exp.get('dates', 'N/A')})")
            print(f"  Education ({len(entry['education'])}):")
            for edu in entry['education'][:2]: # First 2 education entries
                print(f"    - {edu.get('degree', 'N/A')} from {edu.get('university', 'N/A')} ({edu.get('year', 'N/A')})")
