"""HTML newsletter composer."""
from typing import Optional
from jinja2 import Template

from app.models.digest import Digest
from app.core.config import settings


class HTMLComposer:
    """Compose HTML newsletters from digests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize with base URL for images."""
        self.base_url = base_url
    
    def _get_image_url(self, image_path: str) -> str:
        """Convert relative image path to full URL."""
        if not image_path:
            return ""
        if image_path.startswith("http"):
            return image_path
        # Image paths are like /static/images/xyz.png
        return f"{self.base_url}{image_path}"
    
    async def compose(
        self,
        digest: Digest,
        for_preview: bool = False,
        for_email: bool = False,
    ) -> str:
        """Compose an HTML newsletter."""
        
        template = self._get_template(for_email)
        
        papers_data = []
        for dp in digest.digest_papers:
            paper = dp.paper
            papers_data.append({
                "title": paper.title,
                "headline": paper.summary_headline or paper.title,
                "takeaway": paper.summary_takeaway or (paper.abstract[:300] if paper.abstract else ""),
                "why_matters": paper.summary_why_matters or "",
                "credibility_score": paper.credibility_score if paper.credibility_score is not None else 0,
                "credibility_note": paper.credibility_note or "",
                "journal": paper.journal or "Unknown",
                "authors": ", ".join(a.name for a in paper.authors[:3]) if paper.authors else "",
                "url": paper.url or "#",
                "image_path": self._get_image_url(paper.image_path) if paper.image_path else "",
                "tags": paper.tags or [],
                "is_preprint": paper.is_preprint,
            })
        
        html = template.render(
            digest_name=digest.name,
            intro_text=digest.intro_text or "",
            conclusion_text=digest.conclusion_text or "",
            papers=papers_data,
            for_email=for_email,
        )
        
        return html
    
    def _get_template(self, for_email: bool) -> Template:
        """Get the Jinja2 template."""
        
        # Inline CSS for email compatibility
        template_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ digest_name }} - Science Digest</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.7;
            color: #1a1a2e;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
        }
        
        .container {
            max-width: 720px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.2rem;
            font-weight: 400;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .header .subtitle {
            font-size: 1rem;
            opacity: 0.9;
            font-style: italic;
        }
        
        .intro {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            font-size: 1.1rem;
            color: #495057;
        }
        
        .papers {
            padding: 20px 30px;
        }
        
        .paper {
            margin-bottom: 40px;
            padding-bottom: 40px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .paper:last-child {
            border-bottom: none;
            margin-bottom: 20px;
        }
        
        .paper-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .paper-headline {
            font-size: 1.4rem;
            color: #2d3436;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .paper-headline a {
            color: inherit;
            text-decoration: none;
        }
        
        .paper-headline a:hover {
            color: #0984e3;
        }
        
        .paper-meta {
            font-size: 0.85rem;
            color: #74b9ff;
            margin-bottom: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        
        .paper-meta .journal {
            background: #dfe6e9;
            padding: 4px 10px;
            border-radius: 4px;
            color: #636e72;
        }
        
        .paper-meta .preprint-badge {
            background: #fdcb6e;
            color: #2d3436;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 600;
        }
        
        .paper-takeaway {
            font-size: 1.05rem;
            color: #2d3436;
            margin-bottom: 15px;
        }
        
        .paper-why-matters {
            font-size: 0.95rem;
            color: #636e72;
            font-style: italic;
            margin-bottom: 15px;
            padding-left: 15px;
            border-left: 3px solid #74b9ff;
        }
        
        .credibility-box {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .credibility-score {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .score-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .score-high { background: #00b894; color: white; }
        .score-medium { background: #fdcb6e; color: #2d3436; }
        .score-low { background: #e17055; color: white; }
        
        .credibility-note {
            font-size: 0.9rem;
            color: #636e72;
        }
        
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
        }
        
        .tag {
            background: #e9ecef;
            color: #495057;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        
        .conclusion {
            padding: 30px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            font-size: 1.05rem;
            color: #495057;
            text-align: center;
        }
        
        .footer {
            padding: 20px 30px;
            text-align: center;
            font-size: 0.85rem;
            color: #adb5bd;
            background: #2d3436;
        }
        
        .footer a {
            color: #74b9ff;
        }
        
        @media (max-width: 600px) {
            body { padding: 10px; }
            .header h1 { font-size: 1.6rem; }
            .paper-headline { font-size: 1.2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ digest_name }}</h1>
            <div class="subtitle">Science Digest Newsletter</div>
        </div>
        
        {% if intro_text %}
        <div class="intro">
            {{ intro_text }}
        </div>
        {% endif %}
        
        <div class="papers">
            {% for paper in papers %}
            <article class="paper">
                {% if paper.image_path %}
                <img src="{{ paper.image_path }}" alt="{{ paper.headline }}" class="paper-image">
                {% endif %}
                
                <h2 class="paper-headline">
                    <a href="{{ paper.url }}" target="_blank">{{ paper.headline }}</a>
                </h2>
                
                <div class="paper-meta">
                    <span class="journal">{{ paper.journal }}</span>
                    <span class="authors">{{ paper.authors }}</span>
                    {% if paper.is_preprint %}
                    <span class="preprint-badge">PREPRINT</span>
                    {% endif %}
                </div>
                
                <p class="paper-takeaway">{{ paper.takeaway }}</p>
                
                {% if paper.why_matters %}
                <p class="paper-why-matters">{{ paper.why_matters }}</p>
                {% endif %}
                
                <div class="credibility-box">
                    <div class="credibility-score">
                        <span>Credibility:</span>
                        {% if paper.credibility_score >= 70 %}
                        <span class="score-badge score-high">{{ paper.credibility_score|round|int }}/100</span>
                        {% elif paper.credibility_score >= 50 %}
                        <span class="score-badge score-medium">{{ paper.credibility_score|round|int }}/100</span>
                        {% else %}
                        <span class="score-badge score-low">{{ paper.credibility_score|round|int }}/100</span>
                        {% endif %}
                    </div>
                    <p class="credibility-note">{{ paper.credibility_note }}</p>
                </div>
                
                {% if paper.tags %}
                <div class="tags">
                    {% for tag in paper.tags %}
                    <span class="tag">{{ tag }}</span>
                    {% endfor %}
                </div>
                {% endif %}
            </article>
            {% endfor %}
        </div>
        
        {% if conclusion_text %}
        <div class="conclusion">
            {{ conclusion_text }}
        </div>
        {% endif %}
        
        <div class="footer">
            Generated by <a href="#">Science Digest</a> | Stay curious!
        </div>
    </div>
</body>
</html>'''
        
        return Template(template_str)
