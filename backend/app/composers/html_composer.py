"""HTML newsletter composer."""
import re
from typing import Optional
from jinja2 import Template

from app.models.digest import Digest
from app.models.domain_config import DomainConfig


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

    def _parse_conclusion_text(self, text: str) -> str:
        """Parse conclusion text with markdown-like formatting to HTML."""
        if not text:
            return ""

        lines = text.split('\n')
        html_parts = []
        in_list = False

        for line in lines:
            trimmed = line.strip()

            if not trimmed:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                continue

            # Handle bullet points
            if trimmed.startswith('- ') or trimmed.startswith('* ') or trimmed.startswith('• '):
                if not in_list:
                    html_parts.append('<ul class="conclusion-list">')
                    in_list = True
                content = trimmed[2:]
                # Parse bold within bullet
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                html_parts.append(f'<li>{content}</li>')
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False

                # Handle bold headers (**text**)
                if trimmed.startswith('**') and '**' in trimmed[2:]:
                    # Parse all bold sections
                    parsed = re.sub(r'\*\*(.+?)\*\*', r'<strong class="conclusion-header">\1</strong>', trimmed)
                    html_parts.append(f'<p class="conclusion-para">{parsed}</p>')
                else:
                    # Regular paragraph - still parse any inline bold
                    parsed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', trimmed)
                    html_parts.append(f'<p class="conclusion-para">{parsed}</p>')

        if in_list:
            html_parts.append('</ul>')

        return '\n'.join(html_parts)

    async def compose(
        self,
        digest: Digest,
        for_preview: bool = False,
        for_email: bool = False,
        for_pdf: bool = False,
        domain_config: Optional[DomainConfig] = None,
    ) -> str:
        """Compose an HTML newsletter."""

        # Default branding values
        app_name = "Science Digest"
        newsletter_title = "Science Digest Newsletter"
        primary_color = "#0984e3"
        footer_text = "Stay curious!"

        # Override with domain config if provided
        if domain_config:
            app_name = domain_config.app_name
            newsletter_title = domain_config.newsletter_title
            primary_color = domain_config.primary_color
            footer_text = domain_config.footer_text

        template = self._get_template(for_email, for_pdf, primary_color)

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

        # Parse conclusion text to HTML
        conclusion_html = self._parse_conclusion_text(digest.conclusion_text or "")

        html = template.render(
            digest_name=digest.name,
            intro_text=digest.intro_text or "",
            conclusion_html=conclusion_html,
            papers=papers_data,
            for_email=for_email,
            for_pdf=for_pdf,
            app_name=app_name,
            newsletter_title=newsletter_title,
            footer_text=footer_text,
        )

        return html

    def _get_template(self, for_email: bool, for_pdf: bool = False, primary_color: str = "#0984e3") -> Template:
        """Get the Jinja2 template."""

        # PDF-specific styles for xhtml2pdf compatibility
        pdf_image_style = """
            .paper-image {
                width: 400px;
                height: auto;
                max-height: 300px;
                display: block;
                margin: 0 auto 20px auto;
            }
        """ if for_pdf else """
            .paper-image {
                width: 100%;
                height: 250px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        """

        # Inline CSS for email compatibility
        template_str = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ digest_name }}}} - {{{{ app_name }}}}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.7;
            color: #1a1a2e;
            background: {"#ffffff" if for_pdf else "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"};
            padding: {"10px" if for_pdf else "20px"};
        }}

        .container {{
            max-width: {"600px" if for_pdf else "720px"};
            margin: 0 auto;
            background: #ffffff;
            {"" if for_pdf else "border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);"}
            overflow: hidden;
        }}

        .header {{
            background: {primary_color if for_pdf else f"linear-gradient(135deg, {primary_color} 0%, #6c5ce7 100%)"};
            color: white;
            padding: {"30px 20px" if for_pdf else "50px 30px"};
            text-align: center;
        }}

        .header h1 {{
            font-size: {"1.8rem" if for_pdf else "2.2rem"};
            font-weight: 400;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            font-size: 1rem;
            opacity: 0.9;
            font-style: italic;
        }}

        .intro {{
            padding: {"20px" if for_pdf else "30px"};
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            font-size: {"1rem" if for_pdf else "1.1rem"};
            color: #495057;
        }}

        .papers {{
            padding: {"15px 20px" if for_pdf else "20px 30px"};
        }}

        .paper {{
            margin-bottom: {"30px" if for_pdf else "40px"};
            padding-bottom: {"30px" if for_pdf else "40px"};
            border-bottom: 1px solid #e9ecef;
            {"page-break-inside: avoid;" if for_pdf else ""}
        }}

        .paper:last-child {{
            border-bottom: none;
            margin-bottom: 20px;
        }}

        {pdf_image_style}

        .paper-headline {{
            font-size: {"1.2rem" if for_pdf else "1.4rem"};
            color: #2d3436;
            margin-bottom: 12px;
            line-height: 1.4;
        }}

        .paper-headline a {{
            color: inherit;
            text-decoration: none;
        }}

        .paper-headline a:hover {{
            color: {primary_color};
        }}

        .paper-meta {{
            font-size: 0.85rem;
            color: #636e72;
            margin-bottom: 15px;
        }}

        .paper-meta .journal {{
            background: #dfe6e9;
            padding: 4px 10px;
            {"" if for_pdf else "border-radius: 4px;"}
            color: #636e72;
            display: inline-block;
            margin-right: 10px;
        }}

        .paper-meta .authors {{
            color: #636e72;
        }}

        .paper-meta .preprint-badge {{
            background: #fdcb6e;
            color: #2d3436;
            padding: 4px 10px;
            {"" if for_pdf else "border-radius: 4px;"}
            font-weight: 600;
            display: inline-block;
            margin-left: 10px;
        }}

        .paper-takeaway {{
            font-size: 1.05rem;
            color: #2d3436;
            margin-bottom: 15px;
        }}

        .paper-why-matters {{
            font-size: 0.95rem;
            color: #636e72;
            font-style: italic;
            margin-bottom: 15px;
            padding-left: 15px;
            border-left: 3px solid #74b9ff;
        }}

        .credibility-box {{
            background: #f8f9fa;
            {"" if for_pdf else "border-radius: 8px;"}
            padding: 15px;
            margin-top: 15px;
        }}

        .credibility-score {{
            margin-bottom: 8px;
        }}

        .score-badge {{
            display: inline-block;
            padding: 4px 12px;
            {"" if for_pdf else "border-radius: 20px;"}
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .score-high {{ background: #00b894; color: white; }}
        .score-medium {{ background: #fdcb6e; color: #2d3436; }}
        .score-low {{ background: #e17055; color: white; }}

        .credibility-note {{
            font-size: 0.9rem;
            color: #636e72;
        }}

        .tags {{
            margin-top: 15px;
        }}

        .tag {{
            background: #e9ecef;
            color: #495057;
            padding: 4px 12px;
            {"" if for_pdf else "border-radius: 20px;"}
            font-size: 0.8rem;
            display: inline-block;
            margin-right: 8px;
            margin-bottom: 8px;
        }}

        .conclusion {{
            padding: {"20px" if for_pdf else "30px"};
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            font-size: 1.05rem;
            color: #495057;
            text-align: left;
            {"page-break-inside: avoid;" if for_pdf else ""}
        }}

        .conclusion h3 {{
            font-size: 1.3rem;
            color: #2d3436;
            margin-bottom: 15px;
            text-align: center;
        }}

        .conclusion-list {{
            margin: 15px 0;
            padding-left: 25px;
        }}

        .conclusion-list li {{
            margin-bottom: 10px;
            color: #495057;
        }}

        .conclusion-para {{
            margin-bottom: 12px;
        }}

        .conclusion-header {{
            color: {primary_color};
            font-size: 1.1rem;
        }}

        .disclaimer {{
            padding: {"15px 20px" if for_pdf else "20px 30px"};
            background: #f1f3f4;
            border-top: 1px solid #e9ecef;
            font-size: 0.8rem;
            color: #6c757d;
            text-align: center;
            {"page-break-inside: avoid;" if for_pdf else ""}
        }}

        .disclaimer p {{
            margin-bottom: 8px;
        }}

        .disclaimer strong {{
            color: #495057;
        }}

        .footer {{
            padding: {"15px 20px" if for_pdf else "20px 30px"};
            text-align: center;
            font-size: 0.85rem;
            color: {"#6c757d" if for_pdf else "#adb5bd"};
            background: {"#e9ecef" if for_pdf else "#2d3436"};
        }}

        .footer a {{
            color: {primary_color if for_pdf else "#74b9ff"};
        }}

        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            .header h1 {{ font-size: 1.6rem; }}
            .paper-headline {{ font-size: 1.2rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{{{ digest_name }}}}</h1>
            <div class="subtitle">{{{{ newsletter_title }}}}</div>
        </div>

        {{% if intro_text %}}
        <div class="intro">
            {{{{ intro_text }}}}
        </div>
        {{% endif %}}

        <div class="papers">
            {{% for paper in papers %}}
            <article class="paper">
                {{% if paper.image_path %}}
                <img src="{{{{ paper.image_path }}}}" alt="{{{{ paper.headline }}}}" class="paper-image">
                {{% endif %}}

                <h2 class="paper-headline">
                    <a href="{{{{ paper.url }}}}" target="_blank">{{{{ paper.headline }}}}</a>
                </h2>

                <div class="paper-meta">
                    <span class="journal">{{{{ paper.journal }}}}</span>
                    <span class="authors">{{{{ paper.authors }}}}</span>
                    {{% if paper.is_preprint %}}
                    <span class="preprint-badge">PREPRINT</span>
                    {{% endif %}}
                </div>

                <p class="paper-takeaway">{{{{ paper.takeaway }}}}</p>

                {{% if paper.why_matters %}}
                <p class="paper-why-matters">{{{{ paper.why_matters }}}}</p>
                {{% endif %}}

                <div class="credibility-box">
                    <div class="credibility-score">
                        <span>Credibility:</span>
                        {{% if paper.credibility_score >= 70 %}}
                        <span class="score-badge score-high">{{{{ paper.credibility_score|round|int }}}}/100</span>
                        {{% elif paper.credibility_score >= 50 %}}
                        <span class="score-badge score-medium">{{{{ paper.credibility_score|round|int }}}}/100</span>
                        {{% else %}}
                        <span class="score-badge score-low">{{{{ paper.credibility_score|round|int }}}}/100</span>
                        {{% endif %}}
                    </div>
                    <p class="credibility-note">{{{{ paper.credibility_note }}}}</p>
                </div>

                {{% if paper.tags %}}
                <div class="tags">
                    {{% for tag in paper.tags %}}
                    <span class="tag">{{{{ tag }}}}</span>
                    {{% endfor %}}
                </div>
                {{% endif %}}
            </article>
            {{% endfor %}}
        </div>

        {{% if conclusion_html %}}
        <div class="conclusion">
            <h3>Final Thoughts</h3>
            {{{{ conclusion_html|safe }}}}
        </div>
        {{% endif %}}

        <div class="disclaimer">
            <p><strong>Disclaimer:</strong> Images in this newsletter are AI-generated illustrations created to complement the research summaries and may not represent actual study visuals.</p>
            <p>Summaries are AI-generated from published research papers. For complete methodology and findings, please refer to the original publications.</p>
        </div>

        <div class="footer">
            Generated by <a href="#">{{{{ app_name }}}}</a> | {{{{ footer_text }}}}
        </div>
    </div>
</body>
</html>'''

        return Template(template_str)
