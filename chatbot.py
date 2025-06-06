from typing import Dict, List, Any, Union
import re

class CVAnalyzer:
    def __init__(self):
        self.skills_keywords = {
            'technical': [
                'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
                'aws', 'docker', 'kubernetes', 'git', 'linux', 'html', 'css',
                'machine learning', 'data science', 'tensorflow', 'pytorch',
                'api', 'rest', 'microservices', 'agile', 'scrum'
            ],
            'soft': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'creative', 'adaptable', 'organized', 'detail-oriented',
                'collaborative', 'innovative', 'strategic', 'mentoring'
            ],
            'business': [
                'project management', 'budget', 'stakeholder', 'business analysis',
                'process improvement', 'strategy', 'consulting', 'client relations',
                'sales', 'marketing', 'finance', 'operations'
            ]
        }
        
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'degree', 'university', 'college',
            'certification', 'course', 'training', 'diploma', 'mba'
        ]
        
        self.experience_keywords = [
            'years', 'experience', 'worked', 'developed', 'managed', 'led',
            'implemented', 'designed', 'created', 'built', 'analyzed'
        ]

    def extract_text_sections(self, cv_text: str) -> Dict[str, str]:
        """Extract different sections from CV text"""
        cv_lower = cv_text.lower()
        sections = {
            'contact': '',
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'full_text': cv_text
        }
        
        # Simple section extraction based on common headers
        section_patterns = {
            'experience': r'(experience|work history|employment|professional experience)(.*?)(?=education|skills|projects|$)',
            'education': r'(education|academic|qualification)(.*?)(?=experience|skills|projects|$)',
            'skills': r'(skills|technical skills|competencies)(.*?)(?=experience|education|projects|$)',
            'summary': r'(summary|objective|profile|about)(.*?)(?=experience|education|skills|$)'
        }
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, cv_lower, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(2).strip()
        
        return sections

    def analyze_skills(self, cv_text: str) -> Dict[str, Any]:
        """Analyze skills mentioned in CV"""
        cv_lower = cv_text.lower()
        found_skills = {
            'technical': [],
            'soft': [],
            'business': []
        }
        
        for category, skills in self.skills_keywords.items():
            for skill in skills:
                if skill in cv_lower:
                    found_skills[category].append(skill)
        
        return {
            'found_skills': found_skills,
            'total_skills': sum(len(skills) for skills in found_skills.values()),
            'skill_diversity': len([cat for cat, skills in found_skills.items() if skills])
        }

    def analyze_experience(self, cv_text: str) -> Dict[str, Any]:
        """Analyze work experience"""
        cv_lower = cv_text.lower()
        
        # Look for years of experience
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience.*?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?'
        ]
        
        years_mentioned = []
        for pattern in year_patterns:
            matches = re.findall(pattern, cv_lower)
            years_mentioned.extend([int(match) for match in matches])
        
        # Count action verbs
        action_verbs = [
            'developed', 'managed', 'led', 'implemented', 'designed', 'created',
            'built', 'analyzed', 'improved', 'optimized', 'delivered', 'achieved'
        ]
        
        action_count = sum(1 for verb in action_verbs if verb in cv_lower)
        
        # Look for quantified achievements
        number_patterns = [
            r'\d+%', r'\$\d+', r'\d+k', r'\d+\+', r'\d+ team', r'\d+ projects'
        ]
        quantified_achievements = sum(1 for pattern in number_patterns 
                                    for _ in re.findall(pattern, cv_lower))
        
        return {
            'years_experience': max(years_mentioned) if years_mentioned else 0,
            'action_verbs_count': action_count,
            'quantified_achievements': quantified_achievements,
            'has_leadership_experience': any(word in cv_lower for word in ['led', 'managed', 'supervised', 'directed'])
        }

    def analyze_education(self, cv_text: str) -> Dict[str, Any]:
        """Analyze education background"""
        cv_lower = cv_text.lower()
        
        education_levels = {
            'phd': 4, 'doctorate': 4, 'doctoral': 4,
            'master': 3, 'mba': 3, 'ms': 3, 'ma': 3,
            'bachelor': 2, 'bs': 2, 'ba': 2, 'bsc': 2,
            'associate': 1, 'diploma': 1
        }
        
        highest_education = 0
        found_degrees = []
        
        for degree, level in education_levels.items():
            if degree in cv_lower:
                highest_education = max(highest_education, level)
                found_degrees.append(degree)
        
        certifications = sum(1 for cert in ['certification', 'certified', 'certificate'] 
                       if cert in cv_lower)
        
        return {
            'highest_education_level': highest_education,
            'degrees_found': found_degrees,
            'certifications_count': certifications,
            'has_relevant_education': highest_education >= 2
        }

    def analyze_cv_structure(self, cv_text: str) -> Dict[str, Any]:
        """Analyze CV structure and formatting"""
        lines = cv_text.split('\n')
        
        # Check for contact information
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,14}'
        
        has_email = bool(re.search(email_pattern, cv_text))
        has_phone = bool(re.search(phone_pattern, cv_text))
        
        # Check for common sections
        section_headers = ['experience', 'education', 'skills', 'summary', 'objective']
        sections_present = sum(1 for header in section_headers if header in cv_text.lower())
        
        return {
            'word_count': len(cv_text.split()),
            'line_count': len(lines),
            'has_contact_info': has_email and has_phone,
            'sections_present': sections_present,
            'structure_score': min(10, sections_present * 2)
        }

    def generate_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate list of strengths based on analysis"""
        strengths = []
        
        skills_analysis = analysis['skills']
        experience_analysis = analysis['experience']
        education_analysis = analysis['education']
        structure_analysis = analysis['structure']
        
        # Skills strengths
        if skills_analysis['total_skills'] > 10:
            strengths.append("Strong technical skill set with diverse competencies")
        
        if skills_analysis['skill_diversity'] >= 3:
            strengths.append("Well-rounded profile with technical, soft, and business skills")
        
        # Experience strengths
        if experience_analysis['years_experience'] > 5:
            strengths.append(f"Extensive professional experience ({experience_analysis['years_experience']} years)")
        
        if experience_analysis['action_verbs_count'] > 8:
            strengths.append("Strong use of action-oriented language showcasing achievements")
        
        if experience_analysis['quantified_achievements'] > 3:
            strengths.append("Excellent use of quantified achievements and metrics")
        
        if experience_analysis['has_leadership_experience']:
            strengths.append("Demonstrated leadership and management experience")
        
        # Education strengths
        if education_analysis['highest_education_level'] >= 3:
            strengths.append("Advanced educational background")
        
        if education_analysis['certifications_count'] > 2:
            strengths.append("Strong commitment to professional development through certifications")
        
        # Structure strengths
        if structure_analysis['has_contact_info']:
            strengths.append("Complete contact information provided")
        
        if structure_analysis['sections_present'] >= 4:
            strengths.append("Well-organized CV structure with clear sections")
        
        if not strengths:
            strengths.append("Shows initiative in seeking career development feedback")
        
        return strengths

    def generate_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate list of areas for improvement"""
        improvements = []
        
        skills_analysis = analysis['skills']
        experience_analysis = analysis['experience']
        education_analysis = analysis['education']
        structure_analysis = analysis['structure']
        
        # Skills improvements
        if skills_analysis['total_skills'] < 5:
            improvements.append("Consider adding more relevant technical and soft skills")
        
        if not skills_analysis['found_skills']['soft']:
            improvements.append("Include soft skills like communication, leadership, and teamwork")
        
        if skills_analysis['skill_diversity'] < 2:
            improvements.append("Diversify skill set across technical, soft, and business competencies")
        
        # Experience improvements
        if experience_analysis['action_verbs_count'] < 5:
            improvements.append("Use more action verbs to describe your achievements (developed, managed, implemented)")
        
        if experience_analysis['quantified_achievements'] < 2:
            improvements.append("Add quantified achievements with specific numbers, percentages, or metrics")
        
        if not experience_analysis['has_leadership_experience'] and experience_analysis['years_experience'] > 3:
            improvements.append("Highlight any leadership or mentoring experiences you may have")
        
        # Education improvements
        if education_analysis['certifications_count'] == 0:
            improvements.append("Consider adding relevant professional certifications")
        
        # Structure improvements
        if not structure_analysis['has_contact_info']:
            improvements.append("Ensure complete contact information (email and phone) is included")
        
        if structure_analysis['sections_present'] < 3:
            improvements.append("Organize CV with clear sections: Summary, Experience, Education, Skills")
        
        if structure_analysis['word_count'] < 200:
            improvements.append("Expand content to provide more detailed descriptions of your experience")
        elif structure_analysis['word_count'] > 800:
            improvements.append("Consider condensing content to keep CV concise and focused")
        
        if not improvements:
            improvements.append("Consider tailoring your CV for specific job applications")
        
        return improvements

    def calculate_overall_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate overall CV score out of 100"""
        skills_score = min(25, analysis['skills']['total_skills'] * 2)
        experience_score = min(25, analysis['experience']['action_verbs_count'] * 2 + 
                          analysis['experience']['quantified_achievements'] * 3)
        education_score = min(25, analysis['education']['highest_education_level'] * 6 + 
                         analysis['education']['certifications_count'] * 3)
        structure_score = min(25, analysis['structure']['structure_score'] * 2.5)
        
        return int(skills_score + experience_score + education_score + structure_score)

    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """Main method to analyze CV and return comprehensive feedback"""
        if not cv_text or len(cv_text.strip()) < 50:
            return {
                'error': 'CV text is too short or empty. Please provide a more detailed CV.'
            }
        
        # Extract sections
        sections = self.extract_text_sections(cv_text)
        
        # Perform analysis
        skills_analysis = self.analyze_skills(cv_text)
        experience_analysis = self.analyze_experience(cv_text)
        education_analysis = self.analyze_education(cv_text)
        structure_analysis = self.analyze_cv_structure(cv_text)
        
        analysis = {
            'skills': skills_analysis,
            'experience': experience_analysis,
            'education': education_analysis,
            'structure': structure_analysis
        }
        
        # Generate feedback
        strengths = self.generate_strengths(analysis)
        improvements = self.generate_improvements(analysis)
        overall_score = self.calculate_overall_score(analysis)
        
        return {
            'overall_score': overall_score,
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'detailed_analysis': {
                'skills_found': skills_analysis['found_skills'],
                'experience_metrics': {
                    'years_of_experience': experience_analysis['years_experience'],
                    'action_verbs_used': experience_analysis['action_verbs_count'],
                    'quantified_achievements': experience_analysis['quantified_achievements']
                },
                'education_level': education_analysis['highest_education_level'],
                'structure_quality': structure_analysis['structure_score']
            }
        }