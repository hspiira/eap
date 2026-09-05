"""
Industry Seed Data

Default industries to be created for each new tenant.
"""

from typing import TypedDict


class IndustrySeedData(TypedDict, total=False):
    """Type definition for industry seed data."""

    name: str
    code: str
    description: str
    children: list["IndustrySeedData"]


INDUSTRIES: list[IndustrySeedData] = [
    {
        "name": "Agriculture & Agribusiness",
        "code": "AGR",
        "description": "Crop production, livestock farming, agricultural machinery, agrochemicals, food processing",
        "children": [
            {
                "name": "Crop Production",
                "code": "AGR-CRP",
                "description": "Commercial and sustainable crop cultivation, harvest management, post-harvest processing, and agricultural yield optimization",
            },
            {
                "name": "Livestock Farming",
                "code": "AGR-LST",
                "description": "Animal husbandry, livestock management, breeding programs, and sustainable farming practices",
            },
            {
                "name": "Agricultural Machinery",
                "code": "AGR-MCH",
                "description": "Manufacturing and distribution of farming equipment, irrigation systems, and agricultural automation solutions",
            },
            {
                "name": "Agrochemicals",
                "code": "AGR-CHM",
                "description": "Production and distribution of fertilizers, pesticides, and other agricultural chemical products",
            },
            {
                "name": "Food Processing",
                "code": "AGR-FOD",
                "description": "Processing, packaging, and preservation of agricultural products for commercial distribution",
            },
        ],
    },
    {
        "name": "Automotive",
        "code": "AUT",
        "description": "Vehicle manufacturing, auto parts production, car sales and dealerships, automotive services",
        "children": [
            {
                "name": "Vehicle Manufacturing",
                "code": "AUT-MFG",
                "description": "Design, engineering, and production of passenger vehicles, commercial vehicles, and automotive components",
            },
            {
                "name": "Auto Parts Production",
                "code": "AUT-PRT",
                "description": "Manufacturing of automotive components, spare parts, and aftermarket products",
            },
            {
                "name": "Car Sales and Dealerships",
                "code": "AUT-SLS",
                "description": "Retail and wholesale distribution of new and used vehicles, dealership management, and automotive sales services",
            },
            {
                "name": "Automotive Services",
                "code": "AUT-SVC",
                "description": "Vehicle maintenance, repair services, diagnostic testing, and automotive technical support",
            },
        ],
    },
    {
        "name": "Aerospace & Defense",
        "code": "AER",
        "description": "Aircraft manufacturing, space exploration, military defense systems, aerospace engineering",
        "children": [
            {
                "name": "Aircraft Manufacturing",
                "code": "AER-ACT",
                "description": "Design, development, and production of commercial and military aircraft, including components and systems",
            },
            {
                "name": "Space Exploration",
                "code": "AER-SPC",
                "description": "Spacecraft development, satellite systems, space mission operations, and space technology research",
            },
            {
                "name": "Military Defense Systems",
                "code": "AER-DEF",
                "description": "Development and production of defense systems, military aircraft, and defense technology solutions",
            },
            {
                "name": "Aerospace Engineering",
                "code": "AER-ENG",
                "description": "Aerospace system design, structural engineering, propulsion systems, and aerospace technology development",
            },
        ],
    },
    {
        "name": "Financial Services",
        "code": "FIN",
        "description": "Banking, investment services, insurance, wealth management, credit services",
        "children": [
            {
                "name": "Banking",
                "code": "FIN-BNK",
                "description": "Retail and commercial banking services, financial transactions, and banking technology solutions",
            },
            {
                "name": "Investment Services",
                "code": "FIN-INV",
                "description": "Investment management, portfolio services, financial advisory, and investment technology platforms",
            },
            {
                "name": "Wealth Management",
                "code": "FIN-WLT",
                "description": "Private banking, financial planning, estate management, and high-net-worth client services",
            },
            {
                "name": "Credit Services",
                "code": "FIN-CRD",
                "description": "Credit card services, lending solutions, credit risk management, and financial technology platforms",
            },
        ],
    },
    {
        "name": "Healthcare & Pharmaceuticals",
        "code": "HTH",
        "description": "Hospitals and healthcare facilities, pharmaceutical companies, biotechnology",
        "children": [
            {
                "name": "Hospitals and Healthcare Facilities",
                "code": "HTH-HSP",
                "description": "Medical centers, specialized clinics, healthcare delivery systems, and patient care services",
            },
            {
                "name": "Pharmaceutical Companies",
                "code": "HTH-PHR",
                "description": "Drug development, pharmaceutical manufacturing, clinical research, and healthcare product distribution",
            },
            {
                "name": "Medical Equipment Manufacturing",
                "code": "HTH-EQP",
                "description": "Production of medical devices, diagnostic equipment, and healthcare technology solutions",
            },
        ],
    },
    {
        "name": "Information Technology",
        "code": "ITC",
        "description": "Software development, hardware manufacturing, IT consulting and services",
        "children": [
            {
                "name": "Software Development",
                "code": "ITC-SFT",
                "description": "Custom software development, application programming, system integration, and software solutions",
            },
            {
                "name": "Hardware Manufacturing",
                "code": "ITC-HRD",
                "description": "Computer hardware production, server manufacturing, networking equipment, and IT infrastructure",
            },
            {
                "name": "IT Consulting and Services",
                "code": "ITC-CNS",
                "description": "IT strategy consulting, system implementation, technical support, and managed IT services",
            },
            {
                "name": "Cloud Computing",
                "code": "ITC-CLD",
                "description": "Cloud infrastructure, platform services, software as a service (SaaS), and cloud solutions",
            },
        ],
    },
    {
        "name": "Digital Technology & Innovation",
        "code": "DIG",
        "description": "Emerging technologies, digital transformation, and innovation services",
        "children": [
            {
                "name": "Artificial Intelligence & Machine Learning",
                "code": "DIG-AI",
                "description": "Development and implementation of AI systems, machine learning models, neural networks, and deep learning solutions for business and consumer applications",
            },
            {
                "name": "Blockchain & Web3",
                "code": "DIG-BLK",
                "description": "Blockchain technology development, cryptocurrency solutions, smart contracts, decentralized applications, and Web3 infrastructure",
            },
            {
                "name": "Cybersecurity",
                "code": "DIG-SEC",
                "description": "Security solutions, threat detection systems, vulnerability assessment, compliance management, and digital protection services",
            },
            {
                "name": "Data Science & Analytics",
                "code": "DIG-DAT",
                "description": "Big data analytics, business intelligence solutions, predictive modeling, data visualization, and advanced analytics services",
            },
            {
                "name": "Digital Transformation",
                "code": "DIG-TRF",
                "description": "Digital strategy consulting, process automation, business model innovation, and digital modernization services",
            },
        ],
    },
    {
        "name": "Education",
        "code": "EDU",
        "description": "Schools and universities, e-learning platforms, educational services",
        "children": [
            {
                "name": "Schools and Universities",
                "code": "EDU-SCH",
                "description": "Primary, secondary, and higher education institutions, academic programs, and educational facilities",
            },
            {
                "name": "E-learning Platforms",
                "code": "EDU-ELE",
                "description": "Online education platforms, digital learning solutions, and educational technology services",
            },
            {
                "name": "Educational Services",
                "code": "EDU-SVC",
                "description": "Educational consulting, curriculum development, student services, and educational support",
            },
            {
                "name": "Vocational Training",
                "code": "EDU-VOC",
                "description": "Professional training programs, skill development, certification courses, and career education",
            },
        ],
    },
    {
        "name": "Media & Entertainment",
        "code": "MED",
        "description": "Film and television, music industry, publishing, broadcasting",
        "children": [
            {
                "name": "Film and Television",
                "code": "MED-FTV",
                "description": "Content production, broadcasting, streaming services, and entertainment media distribution",
            },
            {
                "name": "Music Industry",
                "code": "MED-MUS",
                "description": "Music production, recording, distribution, and digital music platform services",
            },
            {
                "name": "Publishing",
                "code": "MED-PUB",
                "description": "Book publishing, digital content creation, media distribution, and publishing services",
            },
            {
                "name": "Broadcasting",
                "code": "MED-BRD",
                "description": "Television and radio broadcasting, content delivery, and media transmission services",
            },
            {
                "name": "Gaming and Esports",
                "code": "MED-GAM",
                "description": "Video game development, esports competitions, gaming platforms, and interactive entertainment",
            },
        ],
    },
    {
        "name": "Telecommunications",
        "code": "TEL",
        "description": "Mobile services, internet providers, satellite and cable TV",
        "children": [
            {
                "name": "Mobile Services",
                "code": "TEL-MOB",
                "description": "Mobile network operations, wireless communications, and mobile technology solutions",
            },
            {
                "name": "Internet Providers",
                "code": "TEL-INT",
                "description": "Internet service provision, broadband solutions, and network infrastructure services",
            },
            {
                "name": "Satellite and Cable TV",
                "code": "TEL-SAT",
                "description": "Satellite communications, cable television services, and broadcast distribution systems",
            },
            {
                "name": "Networking Services",
                "code": "TEL-NET",
                "description": "Network infrastructure, communication systems, and telecommunications technology solutions",
            },
        ],
    },
    {
        "name": "Environmental Services",
        "code": "ENV",
        "description": "Waste management, recycling services, environmental consultancy",
        "children": [
            {
                "name": "Waste Management",
                "code": "ENV-WST",
                "description": "Waste collection, disposal services, and waste management solutions",
            },
            {
                "name": "Recycling Services",
                "code": "ENV-REC",
                "description": "Material recycling, waste processing, and sustainable resource management",
            },
            {
                "name": "Environmental Consultancy",
                "code": "ENV-CNS",
                "description": "Environmental assessment, sustainability consulting, and environmental management services",
            },
            {
                "name": "Water and Air Quality Management",
                "code": "ENV-QAL",
                "description": "Water treatment, air quality control, and environmental monitoring solutions",
            },
            {
                "name": "Renewable Energy Solutions",
                "code": "ENV-REN",
                "description": "Clean energy implementation, sustainable power solutions, and renewable technology",
            },
        ],
    },
    {
        "name": "Legal Services",
        "code": "LEG",
        "description": "Law firms, legal consultancies, corporate law, litigation",
        "children": [
            {
                "name": "Law Firms",
                "code": "LEG-FRM",
                "description": "Legal practice, attorney services, and law firm management",
            },
            {
                "name": "Legal Consultancies",
                "code": "LEG-CNS",
                "description": "Legal advisory services, compliance consulting, and legal strategy development",
            },
            {
                "name": "Corporate Law",
                "code": "LEG-COR",
                "description": "Business law services, corporate governance, and corporate legal solutions",
            },
            {
                "name": "Litigation",
                "code": "LEG-LIT",
                "description": "Legal dispute resolution, court representation, and litigation services",
            },
            {
                "name": "Intellectual Property Services",
                "code": "LEG-IPR",
                "description": "IP protection, patent services, trademark management, and intellectual property law",
            },
        ],
    },
    {
        "name": "Marketing & Advertising",
        "code": "MKT",
        "description": "Digital marketing, branding and PR, advertising agencies",
        "children": [
            {
                "name": "Digital Marketing",
                "code": "MKT-DIG",
                "description": "Online marketing strategies, digital campaign management, and digital advertising solutions",
            },
            {
                "name": "Branding and PR",
                "code": "MKT-BRD",
                "description": "Brand development, public relations, and corporate communications services",
            },
            {
                "name": "Advertising Agencies",
                "code": "MKT-ADV",
                "description": "Creative advertising, campaign development, and marketing communication services",
            },
            {
                "name": "Market Research",
                "code": "MKT-RES",
                "description": "Consumer research, market analysis, and business intelligence services",
            },
            {
                "name": "Event Marketing",
                "code": "MKT-EVT",
                "description": "Event promotion, experiential marketing, and brand activation services",
            },
        ],
    },
    {
        "name": "Mining & Metals",
        "code": "MIN",
        "description": "Mining of natural resources, metal production, resource exploration",
        "children": [
            {
                "name": "Mining of Natural Resources",
                "code": "MIN-NAT",
                "description": "Mineral extraction, resource mining operations, and mining technology solutions",
            },
            {
                "name": "Metal Production",
                "code": "MIN-MET",
                "description": "Metal processing, alloy production, and metal manufacturing services",
            },
            {
                "name": "Resource Exploration",
                "code": "MIN-EXP",
                "description": "Mineral exploration, resource assessment, and geological surveying services",
            },
            {
                "name": "Mineral Processing",
                "code": "MIN-PRC",
                "description": "Ore processing, mineral refinement, and raw material processing solutions",
            },
        ],
    },
    {
        "name": "Public Sector / Government",
        "code": "GOV",
        "description": "Local, state, and national government services, public administration",
        "children": [
            {
                "name": "Local Government Services",
                "code": "GOV-LOC",
                "description": "Municipal services, local administration, and community government operations",
            },
            {
                "name": "State Government Services",
                "code": "GOV-STT",
                "description": "State administration, regional governance, and state-level public services",
            },
            {
                "name": "National Government Services",
                "code": "GOV-NAT",
                "description": "Federal administration, national governance, and government operations",
            },
            {
                "name": "Public Administration",
                "code": "GOV-ADM",
                "description": "Government management, public policy implementation, and administrative services",
            },
            {
                "name": "Regulatory Agencies",
                "code": "GOV-REG",
                "description": "Regulatory oversight, compliance monitoring, and policy enforcement services",
            },
        ],
    },
    {
        "name": "Professional Services",
        "code": "PRF",
        "description": "Consulting, accounting and auditing, legal services, HR",
        "children": [
            {
                "name": "Consulting",
                "code": "PRF-CNS",
                "description": "Business consulting, management advisory, and professional consulting services",
            },
            {
                "name": "Accounting and Auditing",
                "code": "PRF-ACC",
                "description": "Financial accounting, audit services, and financial advisory solutions",
            },
            {
                "name": "Human Resources and Staffing",
                "code": "PRF-HR",
                "description": "HR management, recruitment services, and workforce solutions",
            },
            {
                "name": "Architecture and Engineering",
                "code": "PRF-ENG",
                "description": "Architectural design, engineering services, and construction consulting",
            },
        ],
    },
    {
        "name": "Biotechnology",
        "code": "BIO",
        "description": "Genetic research, bio-pharmaceuticals, medical diagnostics",
        "children": [
            {
                "name": "Genetic Research",
                "code": "BIO-GEN",
                "description": "Genetic engineering, DNA research, and genetic technology development",
            },
            {
                "name": "Bio-pharmaceuticals",
                "code": "BIO-PHR",
                "description": "Biological drug development, biopharmaceutical manufacturing, and medical research",
            },
            {
                "name": "Medical Diagnostics",
                "code": "BIO-DIA",
                "description": "Diagnostic technology, medical testing, and healthcare diagnostics solutions",
            },
            {
                "name": "Agricultural Biotechnology",
                "code": "BIO-AGR",
                "description": "Agricultural biotech solutions, crop improvement, and bio-agricultural products",
            },
        ],
    },
    {
        "name": "Insurance",
        "code": "INS",
        "description": "Life insurance, health insurance, property and casualty insurance",
        "children": [
            {
                "name": "Life Insurance",
                "code": "INS-LIF",
                "description": "Life coverage, policy management, and life insurance solutions",
            },
            {
                "name": "Health Insurance",
                "code": "INS-HLT",
                "description": "Healthcare coverage, medical insurance, and health benefit solutions",
            },
            {
                "name": "Property and Casualty Insurance",
                "code": "INS-PRP",
                "description": "Property coverage, casualty insurance, and risk management solutions",
            },
            {
                "name": "Reinsurance",
                "code": "INS-REI",
                "description": "Risk transfer, reinsurance solutions, and insurance risk management",
            },
            {
                "name": "Insurance Brokerage",
                "code": "INS-BRK",
                "description": "Insurance brokerage services, policy placement, and insurance consulting",
            },
        ],
    },
]
