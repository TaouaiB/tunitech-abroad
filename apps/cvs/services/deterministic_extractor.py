import re
from typing import TypedDict


class CVDeterministicExtractionResult(TypedDict):
    extracted_email: str
    extracted_phone: str
    extracted_linkedin_url: str
    extracted_github_url: str
    extracted_portfolio_url: str
    website_url: str
    extracted_name: str
    extracted_location: str
    french_level: str
    english_level: str
    current_level: str
    estimated_years_experience: float | None
    target_roles: list[str]
    target_type: str
    raw_skills: list[str]
    warnings: list[str]


class CVDeterministicExtractorService:
    @classmethod
    def extract(cls, raw_text: str) -> CVDeterministicExtractionResult:
        result: CVDeterministicExtractionResult = {
            'extracted_email': '',
            'extracted_phone': '',
            'extracted_linkedin_url': '',
            'extracted_github_url': '',
            'extracted_portfolio_url': '',
            'website_url': '',
            'extracted_name': '',
            'extracted_location': '',
            'french_level': '',
            'english_level': '',
            'current_level': '',
            'estimated_years_experience': None,
            'target_roles': [],
            'target_type': '',
            'raw_skills': [],
            'warnings': []
        }
        estimated_years_experience: float | None = None
        target_roles: list[str] = []
        
        # Email
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
        if email_match:
            result['extracted_email'] = email_match.group(0)
            
        # Phone
        phone_match = re.search(r'(\+?\d[ -]?){8,14}\d', raw_text)
        if phone_match:
            result['extracted_phone'] = phone_match.group(0).strip()
            
        # LinkedIn
        linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)', raw_text, re.IGNORECASE)
        if linkedin_match:
            result['extracted_linkedin_url'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
            
        # GitHub
        github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)', raw_text, re.IGNORECASE)
        if github_match:
            result['extracted_github_url'] = f"https://github.com/{github_match.group(1)}"

        # Portfolio / Website
        portfolio_match = None
        # Look for explicit labels
        lines = raw_text.split('\n')
        for i, line in enumerate(lines):
            # Explicit portfolio label
            m_label = re.search(r'(?:portfolio|website|site web)\s*:\s*(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)', line, re.IGNORECASE)
            if m_label:
                portfolio_match = m_label.group(1)
                break
        
        if not portfolio_match:
            # Fallback search, but avoid skills
            forbidden_domains = {'node.js', 'vue.js', 'next.js', 'express.js', 'react.js', 'three.js', 'react', 'django', 'postgresql', 'mysql'}
            for word in raw_text.split():
                word_lower = word.lower()
                if '@' in word or 'linkedin.com' in word_lower or 'github.com' in word_lower:
                    continue
                if any(fd == word_lower or fd == word_lower.rstrip('.,;)') for fd in forbidden_domains):
                    continue
                
                m = re.match(r'^(?:https?://)?(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)$', word)
                if m:
                    candidate = m.group(1).rstrip('.,;)')
                    if candidate.lower() not in forbidden_domains:
                        portfolio_match = candidate
                        break

        if portfolio_match:
            result['extracted_portfolio_url'] = f"https://{portfolio_match}"
            result['website_url'] = result['extracted_portfolio_url']

        # Name
        for line in lines[:8]:
            candidate = line.strip()
            if cls._looks_like_safe_name(candidate):
                result['extracted_name'] = candidate
                break

        # Location
        location_match = re.search(r'(?:location|localisation|adresse)\s*:\s*([^\n\r\|]+)', raw_text, re.IGNORECASE)
        if location_match:
            result['extracted_location'] = location_match.group(1).strip()[:255]
        else:
            for line in lines[:10]:
                parts = re.split(r'\||•', line)
                for part in parts:
                    cleaned = part.strip()
                    # e.g. Tunis, Tunisia or Tunis, Tunisie
                    if re.match(r'^\s*[A-Z][a-zA-ZÀ-ÿ\s]+,\s*[A-Z][a-zA-ZÀ-ÿ\s]+\s*$', cleaned):
                        # skip obvious false positives like "Software Engineer, DigitalBridge Labs"
                        lower_cleaned = cleaned.lower()
                        if 'engineer' not in lower_cleaned and 'developer' not in lower_cleaned and 'university' not in lower_cleaned:
                            result['extracted_location'] = cleaned[:255]
                            break
                if result.get('extracted_location'):
                    break

        # Languages
        fr_match = re.search(r'(?:french|français)\s*:\s*([^\n\r]+)', raw_text, re.IGNORECASE)
        if fr_match:
            lvl = fr_match.group(1).strip().lower()
            if 'native' in lvl or 'maternelle' in lvl:
                result['french_level'] = 'native'
            elif 'fluent' in lvl or 'courant' in lvl or 'professional' in lvl or 'avancé' in lvl:
                result['french_level'] = 'fluent'
            elif 'intermediate' in lvl or 'intermédiaire' in lvl:
                result['french_level'] = 'intermediate'
            elif 'basic' in lvl or 'débutant' in lvl or 'notion' in lvl:
                result['french_level'] = 'basic'

        en_match = re.search(r'(?:english|anglais)\s*:\s*([^\n\r]+)', raw_text, re.IGNORECASE)
        if en_match:
            lvl = en_match.group(1).strip().lower()
            if 'native' in lvl or 'maternelle' in lvl:
                result['english_level'] = 'native'
            elif 'fluent' in lvl or 'courant' in lvl or 'professional' in lvl or 'avancé' in lvl:
                result['english_level'] = 'fluent'
            elif 'intermediate' in lvl or 'intermédiaire' in lvl:
                result['english_level'] = 'intermediate'
            elif 'basic' in lvl or 'débutant' in lvl or 'notion' in lvl:
                result['english_level'] = 'basic'

        # Target Roles
        # Find section header, then read until blank line or another header
        target_role_headers = ['target roles', 'rôles ciblés', 'postes ciblés', 'objectif', 'target position']
        roles_text = ""
        in_roles_section = False
        
        # also check for inline target roles:
        inline_roles = re.search(r'(?:target roles|rôles ciblés|postes ciblés|objectif|target position)\s*:\s*([^\n\r]+)', raw_text, re.IGNORECASE)
        if inline_roles:
            roles_text = inline_roles.group(1)
        else:
            for line in lines:
                cleaned = line.strip()
                lower_cleaned = cleaned.lower()
                
                if not in_roles_section:
                    if any(header == lower_cleaned or lower_cleaned.startswith(header + ":") for header in target_role_headers):
                        in_roles_section = True
                        if ":" in cleaned:
                            roles_text += cleaned.split(":", 1)[1] + " "
                else:
                    if not cleaned or (cleaned.isupper() and len(cleaned) > 4) or cleaned.lower() in ["skills", "compétences", "experience", "expérience", "education", "formation"]:
                        break
                    roles_text += cleaned + ", "
                    
        if roles_text:
            roles = [r.strip() for r in re.split(r',|/| et | and ', roles_text) if r.strip()]
            target_roles = [r for r in roles if len(r) > 2]
            result['target_roles'] = target_roles

        # Years of Experience Estimation
        exp_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:ans?|years?)\s*(?:d\'|\b)(?:expérience|experience)\b', raw_text, re.IGNORECASE)
        if exp_match:
            try:
                estimated_years_experience = float(exp_match.group(1))
                result['estimated_years_experience'] = estimated_years_experience
            except ValueError:
                pass

        # Current Level Estimation
        if estimated_years_experience is not None:
            exp = estimated_years_experience
            if exp < 2:
                result['current_level'] = 'junior'
            elif 2 <= exp < 5:
                result['current_level'] = 'mid'
            else:
                result['current_level'] = 'senior'
        else:
            roles_text_combined = " ".join(target_roles).lower()
            
            # Check explicit job titles in first lines
            first_lines = " ".join(lines[:10]).lower()
            title_match = re.search(r'\b(student|étudiant|junior|senior|lead|intern|stagiaire|stage|mid-level|mid|intermédiaire)\s+(?:developer|engineer|designer|développeur|ingénieur|full\s*stack|front\s*end|back\s*end)\b', first_lines)
            
            if title_match:
                lvl = title_match.group(1)
                if lvl in ['student', 'étudiant']:
                    result['current_level'] = 'student'
                elif lvl in ['intern', 'stagiaire', 'stage']:
                    result['current_level'] = 'intern'
                elif lvl == 'junior':
                    result['current_level'] = 'junior'
                elif lvl in ['senior', 'lead']:
                    result['current_level'] = 'senior'
                elif lvl in ['mid-level', 'mid', 'intermédiaire']:
                    result['current_level'] = 'mid'
            elif 'student' in roles_text_combined or 'étudiant' in roles_text_combined:
                result['current_level'] = 'student'
            elif 'intern' in roles_text_combined or 'stagiaire' in roles_text_combined or 'stage' in roles_text_combined:
                result['current_level'] = 'intern'
            elif 'junior' in roles_text_combined:
                result['current_level'] = 'junior'
            elif 'senior' in roles_text_combined or 'lead' in roles_text_combined:
                result['current_level'] = 'senior'

        # Skills
        skill_candidates = set()
        in_skills_section = False
        noise_words = {
            "projects", "education", "experience", "private", "university", "target", "roles", "salary", "range", 
            "march", "january", "february", "april", "may", "june", "july", "august", "september", "october", "november", "december", 
            "and", "role", "tunis", "tunisia", "france", "belgium", "luxembourg", "canada", "local", "clients", 
            "digitalbridge", "labs", "professional", "certifications", "languages", "error", "cases"
        }
        
        for line in lines:
            lower_line = line.lower()
            if any(h in lower_line for h in ["skill", "compétence", "competence"]):
                if not lower_line.startswith("no "):
                    in_skills_section = True
                    # if inline skills e.g. Skills: Python, Django
                    if ":" in lower_line:
                        parts = re.split(r'[,•|-]', line.split(":", 1)[1])
                        for p in parts:
                            c = p.strip()
                            if 1 < len(c) < 30:
                                skill_candidates.add(c)
                    continue
            
            is_comma_separated = line.count(',') >= 2
            
            if in_skills_section or is_comma_separated:
                if in_skills_section and len(line.strip()) == 0:
                    in_skills_section = False
                else:
                    if any(nw in lower_line for nw in ["projects", "education", "target roles:", "salary range", "private university", "french:", "english:", "added filters by"]):
                        continue
                    if line.isupper() and len(line.strip()) > 5:
                        continue # Skip uppercase section headers
                        
                    parts = re.split(r'[,•|-]', line)
                    for p in parts:
                        cleaned = p.strip()
                        if 1 < len(cleaned) < 30:
                            cleaned_lower = cleaned.lower()
                            # Check if it contains any noise words as whole words
                            words = cleaned_lower.split()
                            if any(w in noise_words for w in words):
                                continue
                            if len(words) <= 3 and not re.search(r'\b(19|20)\d{2}\b', cleaned):
                                skill_candidates.add(cleaned)
                            
        result['raw_skills'] = list(skill_candidates)
        
        if not result['extracted_email'] and not result['extracted_phone']:
            result['warnings'].append("No contact information found")
            
        return result

    @staticmethod
    def _looks_like_safe_name(value: str) -> bool:
        if not value or len(value) > 80:
            return False
        if any(token in value.lower() for token in ("@", "http", "linkedin", "github", "cv", "resume", "target", "roles", "salary", "tunis", "tunisia", "france")):
            return False
        words = value.split()
        if not 2 <= len(words) <= 4:
            return False
        return all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+", word) for word in words)
