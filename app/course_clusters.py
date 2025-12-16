"""Course clustering configuration for UVA CS program requirements.

Courses within the same cluster are considered semantically similar,
even if their content descriptions differ. This helps group related
courses together in the vector space.
"""

# Course clusters based on UVA CS degree requirements
# https://records.ureg.virginia.edu/preview_program.php?catoid=67&poid=10221&hl=cs&returnto=search

COURSE_CLUSTERS = {
    # Core Computer Science Foundation (required for all CS majors)
    "cs_core_foundation": [
        "CS 1110", "CS 1111", "CS 1112", "CS 1113",  # Intro Programming
        "CS 2100", "CS 2110",  # Data Structures & Discrete Math
        "CS 2130",  # Computer Systems
        "CS 2150",  # Program & Data Representation
        "CS 3100", "CS 3101", "CS 3102",  # Theory of Computation
        "CS 3200", "CS 3205",  # Software Engineering
        "CS 3240", "CS 3250",  # Advanced Software Development
    ],

    # Algorithms & Theory
    "cs_algorithms_theory": [
        "CS 4100", "CS 4102",  # Algorithms
        "CS 4150",  # Theory of Computation
        "CS 4160",  # Formal Languages
        "CS 4190",  # Automata & Computability
    ],

    # Systems & Architecture
    "cs_systems_architecture": [
        "CS 3330",  # Computer Architecture
        "CS 4414",  # Operating Systems
        "CS 4457",  # Parallel Computing
        "CS 4610",  # Computer Networks
        "CS 4630",  # Network Security
        "CS 4740",  # Cloud Computing
    ],

    # AI & Machine Learning
    "cs_ai_ml": [
        "CS 3710",  # Knowledge-Based AI
        "CS 3750",  # Neural Networks
        "CS 3770",  # Introduction to Cognitive Science
        "CS 4404", "CS 4414", "CS 4420",  # Robotics
        "CS 4710",  # Natural Language Processing
        "CS 4750", "CS 4753",  # Machine Learning
        "CS 4770",  # Computer Vision
        "CS 4774",  # Machine Learning
        "CS 4780",  # Introduction to Machine Learning
        "CS 4810",  # Social and Information Network Analysis
        "CS 4820",  # Bio-inspired Computing
        "CS 4830",  # Computational Biology
    ],

    # Data Science & Databases
    "cs_data_databases": [
        "CS 3710",  # Knowledge-Based AI (overlaps with AI)
        "CS 4501",  # Database Systems
        "CS 4550",  # Data Visualization
        "CS 4750", "CS 4753",  # Machine Learning
        "CS 4774",  # Machine Learning
        "CS 4780",  # Introduction to Machine Learning
        "CS 4810",  # Social and Information Network Analysis
        "STAT 4630",  # Statistics for Data Science
    ],

    # Security & Cryptography
    "cs_security_crypto": [
        "CS 4414",  # Operating Systems Security
        "CS 4501",  # Database Security
        "CS 4630",  # Network Security
        "CS 4680",  # Cryptography
        "CS 4690",  # Information Security
    ],

    # Software Engineering & Development
    "cs_software_engineering": [
        "CS 3200", "CS 3205",  # Software Engineering
        "CS 3240", "CS 3250",  # Advanced Software Development
        "CS 4740",  # Cloud Computing
        "CS 4750",  # Data Science Software
    ],

    # Mathematics Prerequisites (required for CS)
    "cs_math_prerequisites": [
        "MATH 1310", "MATH 1320",  # Calculus I & II
        "MATH 2310",  # Multivariable Calculus
        "APMA 3080", "APMA 3100",  # Linear Algebra
        "APMA 3120",  # Probability
        "MATH 3250", "STAT 3120",  # Statistics/Probability
    ],

    # Science Prerequisites (required for CS)
    "cs_science_prerequisites": [
        "PHYS 1425", "PHYS 1429", "PHYS 2415", "PHYS 2419",  # Physics I & II
        "CHEM 1410", "CHEM 1411", "CHEM 1420", "CHEM 1421",  # Chemistry I & II
        "BIOL 2100",  # Cell Biology
    ],
}

# Cluster descriptions for better understanding
CLUSTER_DESCRIPTIONS = {
    "cs_core_foundation": "Core CS courses required for all majors (programming, data structures, theory)",
    "cs_algorithms_theory": "Algorithm design, analysis, and theoretical computer science",
    "cs_systems_architecture": "Computer systems, architecture, operating systems, and networking",
    "cs_ai_ml": "Artificial intelligence, machine learning, computer vision, and robotics",
    "cs_data_databases": "Data science, databases, and data visualization",
    "cs_security_crypto": "Computer security, cryptography, and information assurance",
    "cs_software_engineering": "Software engineering, development practices, and cloud computing",
    "cs_math_prerequisites": "Mathematics courses required or recommended for CS majors",
    "cs_science_prerequisites": "Science courses required or recommended for CS majors",
}

def get_course_clusters(course_code: str) -> list[str]:
    """Get all clusters that a course belongs to.

    Args:
        course_code: Course code like "CS 4774"

    Returns:
        List of cluster names this course belongs to
    """
    clusters = []
    for cluster_name, courses in COURSE_CLUSTERS.items():
        if course_code in courses:
            clusters.append(cluster_name)
    return clusters

def get_cluster_description(cluster_name: str) -> str:
    """Get human-readable description of a cluster.

    Args:
        cluster_name: Name of the cluster

    Returns:
        Description string
    """
    return CLUSTER_DESCRIPTIONS.get(cluster_name, cluster_name)
