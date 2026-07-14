import re
from typing import TypedDict

from apps.skills.services.ambiguity import is_metadata_noise


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
    warnings: list[str]
    name_confidence: int
    email_confidence: int
    phone_confidence: int
    url_confidence: int


from apps.cvs.services.name_extraction import CVNameExtractionService

class CVDeterministicExtractorService:
    SKILL_SECTION_HEADERS = {
        "skills",
        "technical skills",
        "competences",
        "competences techniques",
        "compétences",
        "compétences techniques",
        "stack",
        "technologies",
        "tools",
        "frameworks",
        "databases",
        "cloud",
        "devops",
        "testing",
        "programming languages",
        "languages / programming languages",
    }
    STOP_SECTION_HEADERS = {
        "experience",
        "professional experience",
        "expérience",
        "expérience professionnelle",
        "projects",
        "projets",
        "education",
        "formation",
        "certifications",
        "contact",
        "profile",
        "profil",
        "summary",
        "résumé",
        "resume",
        "languages",
        "langues",
        "interests",
        "centres d'intérêt",
        "centres d interet",
        "french",
        "français",
        "francais",
        "english",
        "anglais",
    }
    SKILL_SUBSECTION_LABELS = {
        "backend",
        "frontend",
        "front end",
        "back end",
        "databases",
        "database",
        "frameworks",
        "tools",
        "cloud",
        "devops",
        "testing",
        "languages",
        "programming languages",
        "mobile",
        "security",
        "data",
    }
    CV_SKILL_NOISE_TERMS = {
        "api smoke tests",
        "authentication flows",
        "based access control",
        "bug reports",
        "freelance web developer",
        "implemented input validation",
        "inventory manager api",
        "language extraction",
        "location extraction",
        "manual qa",
        "recommended learning topics",
        "responsive ui",
        "seo metadata",
        "server",
        "stock alerts",
        "stock movements",
        "suppliers",
        "testing",
        "tools",
        "validation",
        "web development",
        "and role",
    }
    NON_SKILL_SINGLE_WORDS = {
        "april",
        "august",
        "december",
        "february",
        "january",
        "july",
        "june",
        "march",
        "may",
        "november",
        "october",
        "september",
    }
    SKILL_LIST_SPLIT_RE = re.compile(r"[,•;|/]+")

    @classmethod
    def _header_key(cls, line: str) -> str:
        cleaned = line.strip().strip(":").lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @classmethod
    def _is_skill_section_header(cls, line: str) -> bool:
        key = cls._header_key(line)
        if key in cls.SKILL_SECTION_HEADERS:
            return True
        if ":" in line:
            label = cls._header_key(line.split(":", 1)[0])
            return label in cls.SKILL_SECTION_HEADERS
        return False

    @classmethod
    def _is_stop_section_header(cls, line: str) -> bool:
        key = cls._header_key(line)
        if key in cls.STOP_SECTION_HEADERS:
            return True
        if ":" in line:
            label = cls._header_key(line.split(":", 1)[0])
            return label in cls.STOP_SECTION_HEADERS
        if line.strip().isupper() and len(line.strip()) > 4:
            return True
        return False

    @classmethod
    def _clean_skill_candidate(cls, value: str) -> str:
        cleaned = value.strip().strip(":-–—•*·")
        cleaned = re.sub(r"^\s*[-*]\s*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def _is_reliable_skill_candidate(cls, value: str) -> bool:
        cleaned = cls._clean_skill_candidate(value)
        if not 1 < len(cleaned) <= 50:
            return False
        if is_metadata_noise(cleaned):
            return False
        normalized = cls._header_key(cleaned.rstrip("."))
        if normalized in cls.CV_SKILL_NOISE_TERMS or normalized in cls.STOP_SECTION_HEADERS:
            return False
        if normalized in cls.NON_SKILL_SINGLE_WORDS:
            return False
        if normalized.startswith(("french ", "francais ", "français ", "english ", "anglais ")):
            return False
        if re.search(r"\b(19|20)\d{2}\b", cleaned):
            return False
        if re.search(r"\b(?:implemented|built|created|managed|added|fixed|wrote|developed|designed)\b", normalized):
            return False
        if len(normalized.split()) > 4:
            return False
        return True

    @classmethod
    def _extract_skill_candidates(cls, lines: list[str]) -> tuple[list[str], list[str], bool, bool]:
        candidates: list[str] = []
        seen: set[str] = set()
        warnings: list[str] = []
        in_skills_section = False
        reliable_section_found = False
        noisy_candidate_seen = False

        def add_candidate(raw_value: str) -> None:
            nonlocal noisy_candidate_seen
            candidate = cls._clean_skill_candidate(raw_value)
            if not candidate:
                return
            if not cls._is_reliable_skill_candidate(candidate):
                noisy_candidate_seen = True
                return
            normalized = cls._header_key(candidate)
            if normalized not in seen:
                candidates.append(candidate)
                seen.add(normalized)

        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                if in_skills_section:
                    in_skills_section = False
                continue

            if cls._is_skill_section_header(cleaned_line):
                reliable_section_found = True
                in_skills_section = True
                if ":" in cleaned_line:
                    inline_value = cleaned_line.split(":", 1)[1]
                    for part in cls.SKILL_LIST_SPLIT_RE.split(inline_value):
                        add_candidate(part)
                continue

            if in_skills_section and cls._is_stop_section_header(cleaned_line):
                in_skills_section = False
                continue

            if not in_skills_section:
                continue

            if ":" in cleaned_line:
                label, values = cleaned_line.split(":", 1)
                if cls._header_key(label) in cls.SKILL_SUBSECTION_LABELS:
                    cleaned_line = values

            parts = cls.SKILL_LIST_SPLIT_RE.split(cleaned_line)
            if len(parts) == 1 and re.search(r"\s{2,}", cleaned_line):
                parts = re.split(r"\s{2,}", cleaned_line)
            for part in parts:
                add_candidate(part)

        if not reliable_section_found:
            warnings.append("no_reliable_skill_section_found")
        if noisy_candidate_seen and not candidates:
            warnings.append("only_broad_or_noisy_skill_candidates_found")
        if not candidates:
            warnings.append("no_skills_detected")

        return candidates, warnings, reliable_section_found, noisy_candidate_seen

    @classmethod
    def extract(cls, raw_text: str, auth_user_name: str = "", user_email: str = "") -> CVDeterministicExtractionResult:
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
            'warnings': [],
            'name_confidence': 0,
            'email_confidence': 0,
            'phone_confidence': 0,
            'url_confidence': 0
        }
        estimated_years_experience: float | None = None
        target_roles: list[str] = []
        
        # Email
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
        if email_match:
            result['extracted_email'] = email_match.group(0)
            result['email_confidence'] = 100
            
        # Phone
        phone_match = re.search(r'(\+?\d[ -]?){8,14}\d', raw_text)
        if phone_match:
            result['extracted_phone'] = phone_match.group(0).strip()
            result['phone_confidence'] = 100
            
        # LinkedIn
        linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)', raw_text, re.IGNORECASE)
        if linkedin_match:
            result['extracted_linkedin_url'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
            result['url_confidence'] = 100
            
        # GitHub
        github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)', raw_text, re.IGNORECASE)
        if github_match:
            result['extracted_github_url'] = f"https://github.com/{github_match.group(1)}"
            result['url_confidence'] = 100

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
            result['url_confidence'] = max(result['url_confidence'], 90)

        # Name
        name_result = CVNameExtractionService.extract(raw_text, auth_user_name, user_email or result['extracted_email'])
        result['extracted_name'] = name_result['value'] or ''
        result['name_confidence'] = name_result['confidence']
        result['warnings'].extend(name_result['warnings'])

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

        raw_skills, skill_warnings, _section_found, _noisy_seen = cls._extract_skill_candidates(lines)
        result['raw_skills'] = raw_skills
        result['warnings'].extend(skill_warnings)
        
        if not result['extracted_email'] and not result['extracted_phone']:
            result['warnings'].append("No contact information found")
            
        return result
