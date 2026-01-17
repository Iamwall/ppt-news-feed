"""Mock data for demo/testing mode."""
from datetime import datetime, timedelta
import random

MOCK_PAPERS = [
    {
        "title": "CRISPR-Cas9 Gene Editing Achieves New Precision in Human Cells",
        "abstract": "We demonstrate a novel approach to CRISPR-Cas9 gene editing that reduces off-target effects by 95% compared to standard methods. Using a modified guide RNA structure and optimized delivery mechanism, we achieved precise edits in human stem cells with unprecedented accuracy. Our method was validated across 50 different gene targets, with consistent results showing minimal unintended modifications. This breakthrough could accelerate the development of gene therapies for genetic disorders.",
        "journal": "Nature Biotechnology",
        "authors": ["Dr. Sarah Chen", "Dr. Michael Roberts", "Dr. Lisa Wong"],
        "source": "pubmed",
        "doi": "10.1038/nbt.2024.001",
        "is_preprint": False,
        "journal_impact_factor": 54.3,
        "citations": 45,
    },
    {
        "title": "Large Language Models Show Emergent Reasoning Capabilities in Scientific Problem Solving",
        "abstract": "This study investigates the emergent reasoning capabilities of large language models (LLMs) when applied to complex scientific problems. We tested GPT-4 and Claude on 1,000 graduate-level physics, chemistry, and biology problems. Results show that chain-of-thought prompting enables models to solve problems requiring multi-step reasoning with 78% accuracy. Importantly, we identify specific failure modes and propose mitigation strategies.",
        "journal": "arXiv",
        "authors": ["Alex Thompson", "Dr. Jennifer Lee", "Prof. David Kim"],
        "source": "arxiv",
        "doi": None,
        "is_preprint": True,
        "journal_impact_factor": None,
        "citations": 12,
    },
    {
        "title": "Climate Change Impact on Global Biodiversity: A Meta-Analysis of 500 Studies",
        "abstract": "We present a comprehensive meta-analysis of 500 peer-reviewed studies examining climate change impacts on biodiversity across terrestrial, freshwater, and marine ecosystems. Our analysis reveals that 68% of studied species show range shifts, with an average poleward movement of 17km per decade. Tropical species face the highest extinction risk, while temperate species show greater adaptive capacity. We provide specific conservation recommendations based on regional vulnerability assessments.",
        "journal": "Science",
        "authors": ["Dr. Emma Watson", "Prof. James Rodriguez", "Dr. Priya Patel"],
        "source": "science_rss",
        "doi": "10.1126/science.2024.123",
        "is_preprint": False,
        "journal_impact_factor": 56.9,
        "citations": 89,
    },
    {
        "title": "Novel mRNA Vaccine Platform Shows Promise Against Multiple Cancer Types",
        "abstract": "Building on mRNA vaccine technology, we developed a personalized cancer vaccine platform that targets patient-specific tumor neoantigens. In Phase I trials with 45 patients across melanoma, lung, and colorectal cancers, we observed complete responses in 22% of patients and partial responses in 40%. The vaccine was well-tolerated with mild side effects. Immune profiling revealed robust CD8+ T cell responses targeting tumor cells.",
        "journal": "Cell",
        "authors": ["Dr. Robert Johnson", "Dr. Maria Garcia", "Dr. Ahmed Hassan"],
        "source": "pubmed",
        "doi": "10.1016/j.cell.2024.001",
        "is_preprint": False,
        "journal_impact_factor": 66.8,
        "citations": 156,
    },
    {
        "title": "Quantum Computing Breakthrough: Error Correction Achieved at Scale",
        "abstract": "We report the first demonstration of fault-tolerant quantum error correction operating below the threshold required for practical quantum computing. Using a 72-qubit superconducting processor, we implemented a distance-5 surface code that maintains logical qubit coherence for over 1 second—a 100x improvement over physical qubits. This milestone brings us closer to scalable, error-corrected quantum computers capable of solving classically intractable problems.",
        "journal": "Nature",
        "authors": ["Prof. John Smith", "Dr. Wei Zhang", "Dr. Anna Kowalski"],
        "source": "nature_rss",
        "doi": "10.1038/nature.2024.567",
        "is_preprint": False,
        "journal_impact_factor": 64.8,
        "citations": 234,
    },
    {
        "title": "Deep Learning Model Predicts Protein-Drug Interactions with 94% Accuracy",
        "abstract": "We introduce DrugBERT, a transformer-based deep learning model that predicts protein-drug binding affinity with unprecedented accuracy. Trained on 2 million protein-ligand pairs, our model achieves 94% accuracy on held-out test sets and correctly identified binding sites in 89% of cases. We demonstrate its utility by identifying 12 novel drug candidates for antibiotic-resistant bacteria, 3 of which showed promising in vitro activity.",
        "journal": "bioRxiv",
        "authors": ["Dr. Yuki Tanaka", "Prof. Carlos Silva", "Dr. Sophie Martin"],
        "source": "biorxiv",
        "doi": "10.1101/2024.01.15.567890",
        "is_preprint": True,
        "journal_impact_factor": None,
        "citations": 8,
    },
    {
        "title": "Microplastics Found in Human Brain Tissue: Implications for Neurological Health",
        "abstract": "This study presents the first systematic analysis of microplastic accumulation in human brain tissue. Analyzing post-mortem samples from 120 individuals, we detected microplastics in 92% of specimens, with concentrations correlating with age and environmental exposure. Experimental models suggest potential neurotoxic effects through oxidative stress and inflammation pathways. While causation remains to be established, our findings highlight an urgent need for further research.",
        "journal": "Environmental Health Perspectives",
        "authors": ["Dr. Laura Anderson", "Dr. Thomas Mueller", "Dr. Kenji Yamamoto"],
        "source": "pubmed",
        "doi": "10.1289/EHP.2024.890",
        "is_preprint": False,
        "journal_impact_factor": 11.0,
        "citations": 67,
    },
    {
        "title": "Revolutionary Solar Cell Design Achieves 47% Efficiency",
        "abstract": "We present a tandem solar cell architecture combining perovskite and silicon layers that achieves 47.1% power conversion efficiency under concentrated sunlight—surpassing the previous record by 3.2 percentage points. The design uses a novel anti-reflection coating and optimized band gap engineering. Stability tests show less than 5% degradation after 1,000 hours of operation. This technology could dramatically reduce the cost of solar energy.",
        "journal": "Science Advances",
        "authors": ["Prof. Helen Park", "Dr. Omar Farouq", "Dr. Nina Petrov"],
        "source": "semantic_scholar",
        "doi": "10.1126/sciadv.2024.789",
        "is_preprint": False,
        "journal_impact_factor": 14.1,
        "citations": 112,
    },
]

MOCK_SUMMARIES = {
    "CRISPR-Cas9": {
        "headline": "CRISPR Gets 95% More Precise, Opening Door to Safer Gene Therapy",
        "takeaway": "Scientists have dramatically improved the accuracy of CRISPR gene editing, reducing unintended DNA changes by 95%. This breakthrough uses modified guide molecules and better delivery methods to make edits only where intended.",
        "why_matters": "Safer gene editing means faster approval of therapies for genetic diseases like sickle cell anemia, muscular dystrophy, and inherited blindness.",
        "tags": ["genetics", "CRISPR", "gene therapy", "biotechnology"],
    },
    "Large Language Models": {
        "headline": "AI Models Now Solve Graduate-Level Science Problems with 78% Accuracy",
        "takeaway": "New research shows that large language models can tackle complex scientific problems—like those on graduate exams—when given step-by-step reasoning prompts. The models solved physics, chemistry, and biology problems with surprising accuracy.",
        "why_matters": "This could transform how scientists use AI as a research assistant, potentially accelerating hypothesis generation and literature analysis.",
        "tags": ["AI", "machine learning", "scientific computing", "LLMs"],
    },
    "Climate Change": {
        "headline": "Massive Study: 68% of Species Already Shifting Due to Climate Change",
        "takeaway": "A comprehensive analysis of 500 studies reveals that most species are already moving to cooler areas, averaging 17km poleward per decade. Tropical species face the highest extinction risk as they run out of cooler places to go.",
        "why_matters": "These findings provide a scientific foundation for prioritizing conservation efforts and designing climate-resilient protected areas.",
        "tags": ["climate change", "biodiversity", "conservation", "ecology"],
    },
    "mRNA Vaccine": {
        "headline": "Personalized Cancer Vaccines Show 62% Response Rate in Early Trials",
        "takeaway": "A new mRNA vaccine platform, customized to each patient's tumor, triggered immune responses that shrank or eliminated tumors in 62% of trial participants across three cancer types.",
        "why_matters": "Building on COVID vaccine technology, this approach could revolutionize cancer treatment by training each patient's immune system to recognize their specific tumor.",
        "tags": ["cancer", "immunotherapy", "mRNA", "clinical trials"],
    },
    "Quantum Computing": {
        "headline": "Quantum Computers Cross Critical Error-Correction Threshold",
        "takeaway": "Researchers have achieved a major milestone: keeping quantum information stable for over a second using error correction—100 times longer than individual qubits alone. This was done on a 72-qubit processor.",
        "why_matters": "This brings practical quantum computing significantly closer, with applications in drug discovery, cryptography, and solving problems impossible for classical computers.",
        "tags": ["quantum computing", "physics", "error correction", "technology"],
    },
    "Deep Learning": {
        "headline": "AI Predicts Drug Binding with 94% Accuracy, Finds New Antibiotics",
        "takeaway": "A new AI model called DrugBERT can predict how drugs interact with proteins with 94% accuracy. It has already identified promising candidates for fighting antibiotic-resistant bacteria.",
        "why_matters": "This could dramatically speed up drug discovery, reducing the typical 10-15 year development timeline and addressing the urgent antibiotic resistance crisis.",
        "tags": ["drug discovery", "AI", "antibiotics", "deep learning"],
    },
    "Microplastics": {
        "headline": "Microplastics Detected in 92% of Human Brain Samples Studied",
        "takeaway": "In a concerning finding, researchers detected tiny plastic particles in brain tissue from 92% of 120 individuals studied. Older people and those with higher environmental exposure had more accumulation.",
        "why_matters": "While health effects are still being studied, this raises urgent questions about long-term neurological impacts and the need for reducing plastic pollution.",
        "tags": ["pollution", "neuroscience", "environmental health", "microplastics"],
    },
    "Solar Cell": {
        "headline": "New Solar Cell Shatters Records with 47% Efficiency",
        "takeaway": "By stacking perovskite and silicon layers with a new anti-reflection coating, scientists achieved 47.1% solar efficiency—the highest ever recorded. The cells also proved durable in long-term tests.",
        "why_matters": "Higher efficiency means more power from less space, potentially making solar energy even cheaper and accelerating the transition away from fossil fuels.",
        "tags": ["solar energy", "renewable energy", "materials science", "sustainability"],
    },
}


def get_mock_papers(count: int = 8) -> list:
    """Get mock papers for demo mode."""
    papers = []
    base_date = datetime.now()
    
    for i, paper_data in enumerate(MOCK_PAPERS[:count]):
        paper = paper_data.copy()
        paper["published_date"] = base_date - timedelta(days=random.randint(1, 14))
        paper["source_id"] = f"MOCK-{i+1:04d}"
        paper["url"] = f"https://example.com/paper/{i+1}"
        papers.append(paper)
    
    return papers


def get_mock_summary(paper_title: str) -> dict:
    """Get mock summary for a paper."""
    # Find matching summary by keyword
    for keyword, summary in MOCK_SUMMARIES.items():
        if keyword.lower() in paper_title.lower():
            return summary
    
    # Default summary
    return {
        "headline": f"Key Findings: {paper_title[:50]}...",
        "takeaway": "This research presents significant findings that advance our understanding of the field. The methodology is sound and results are reproducible.",
        "why_matters": "These findings have important implications for future research and potential real-world applications.",
        "key_takeaways": [
            "**Key Insight 1**: Significant positive correlation observed in the primary variable.",
            "**Key Insight 2**: Methodology demonstrates a new approach to solving this problem.",
            "**Key Insight 3**: Results suggest immediate applications in the relevant industry."
        ],
        "tags": ["research", "science"],
    }


def get_mock_credibility(paper: dict) -> tuple:
    """Generate mock credibility score and breakdown."""
    is_preprint = paper.get("is_preprint", False)
    impact_factor = paper.get("journal_impact_factor")
    citations = paper.get("citations", 0)
    
    # Calculate mock scores
    journal_score = min(100, (impact_factor / 70) * 100) if impact_factor else 50
    peer_review_score = 40 if is_preprint else 100
    citation_score = min(100, 50 + (citations / 5))
    
    # Randomize other factors slightly
    author_score = random.uniform(60, 90)
    method_score = random.uniform(55, 85)
    sample_score = random.uniform(50, 80)
    
    total = (
        journal_score * 0.25 +
        author_score * 0.15 +
        sample_score * 0.20 +
        method_score * 0.20 +
        peer_review_score * 0.10 +
        citation_score * 0.10
    )
    
    breakdown = {
        "journal_impact": {"score": journal_score, "weight": 0.25},
        "author_hindex": {"score": author_score, "weight": 0.15},
        "sample_size": {"score": sample_score, "weight": 0.20},
        "methodology": {"score": method_score, "weight": 0.20},
        "peer_review": {"score": peer_review_score, "weight": 0.10},
        "citation_velocity": {"score": citation_score, "weight": 0.10},
    }
    
    # Generate note
    if total >= 70:
        note = f"This study shows high credibility (score: {total:.0f}/100). Published in a high-impact journal with strong methodology."
    elif total >= 50:
        note = f"This study shows moderate credibility (score: {total:.0f}/100). {'Note: This is a preprint and has not yet been peer-reviewed.' if is_preprint else ''}"
    else:
        note = f"This study shows lower credibility (score: {total:.0f}/100). Results should be interpreted with caution."
    
    return round(total, 1), breakdown, note
