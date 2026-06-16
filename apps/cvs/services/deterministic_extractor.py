import re

class CVDeterministicExtractorService:
    @classmethod
    def extract(cls, raw_text: str) -> dict:
        result = {
            'extracted_email': '',
            'extracted_phone': '',
            'extracted_linkedin_url': '',
            'extracted_github_url': '',
            'extracted_portfolio_url': '',
            'website_url': '',
            'extracted_name': '',
            'extracted_location': '',
            'raw_skills': [],
            'warnings': []
        }
        
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
        if email_match:
            result['extracted_email'] = email_match.group(0)
            
        phone_match = re.search(r'(\+?\d[ -]?){8,14}\d', raw_text)
        if phone_match:
            result['extracted_phone'] = phone_match.group(0).strip()
            
        linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)', raw_text)
        if linkedin_match:
            result['extracted_linkedin_url'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
            
        github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)', raw_text)
        if github_match:
            result['extracted_github_url'] = f"https://github.com/{github_match.group(1)}"

        portfolio_match = None
        for word in raw_text.split():
            if '@' in word or 'linkedin.com' in word or 'github.com' in word:
                continue
            m = re.match(r'^(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)$', word)
            if m:
                portfolio_match = m
                break
                
        if portfolio_match:
            url = portfolio_match.group(1).rstrip('.,;)')
            result['extracted_portfolio_url'] = f"https://{url}"
            result['website_url'] = result['extracted_portfolio_url']

        for line in raw_text.split('\n')[:8]:
            candidate = line.strip()
            if cls._looks_like_safe_name(candidate):
                result['extracted_name'] = candidate
                break

        location_match = re.search(r'(?:location|localisation|adresse)\s*:\s*([^\n\r]+)', raw_text, re.IGNORECASE)
        if location_match:
            result['extracted_location'] = location_match.group(1).strip()[:255]
        else:
            for line in raw_text.split('\n')[1:5]:
                if re.match(r'^[A-Za-z\s]+,\s*[A-Za-z\s]+$', line.strip()):
                    result['extracted_location'] = line.strip()[:255]
                    break
            
        skill_candidates = set()
        lines = raw_text.split('\n')
        in_skills_section = False
        noise_words = {"projects", "education", "experience", "private", "university", "target", "roles:", "salary", "range", "march", "january", "february", "april", "may", "june", "july", "august", "september", "october", "november", "december"}
        for line in lines:
            lower_line = line.lower()
            if "skill" in lower_line or "compétence" in lower_line or "competence" in lower_line:
                in_skills_section = True
                continue
            
            is_comma_separated = line.count(',') >= 2
            
            if in_skills_section or is_comma_separated:
                if in_skills_section and len(line.strip()) == 0:
                    in_skills_section = False
                else:
                    if any(nw in lower_line for nw in ["projects", "education", "target roles:", "salary range", "private university"]):
                        continue
                    parts = re.split(r'[,•|-]', line)
                    for p in parts:
                        cleaned = p.strip()
                        if 1 < len(cleaned) < 30 and not any(nw == cleaned.lower() for nw in noise_words):
                            if not re.search(r'\b(19|20)\d{2}\b', cleaned):
                                skill_candidates.add(cleaned)
                            
        result['raw_skills'] = list(skill_candidates)
        
        if not result['extracted_email'] and not result['extracted_phone']:
            result['warnings'].append("No contact information found")
            
        return result

    @staticmethod
    def _looks_like_safe_name(value: str) -> bool:
        if not value or len(value) > 80:
            return False
        if any(token in value.lower() for token in ("@", "http", "linkedin", "github", "cv", "resume")):
            return False
        words = value.split()
        if not 2 <= len(words) <= 4:
            return False
        return all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+", word) for word in words)
