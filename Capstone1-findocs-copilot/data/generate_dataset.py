import json

def generate_sec_dataset():
    documents = [
        # =========================================================
        # NVIDIA (NVDA)
        # =========================================================
        {
            "doc_id": "NVDA-2024-10K-RISKS",
            "ticker": "NVDA",
            "company": "NVIDIA Corporation",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 1A - Risk Factors",
            "title": "NVIDIA FY2024 10-K Risk Factors: Export Controls and Supply Chain Constraints",
            "text": (
                "Our business is subject to significant risks regarding U.S. export controls and trade regulations "
                "concerning advanced integrated circuits and semiconductor manufacturing equipment to China and other "
                "restricted destinations. On October 17, 2023, the U.S. government issued interim final rules amending "
                "export controls on advanced computing items, which restricted exports of our A100, A800, H100, H800, "
                "L40, L40S, and RTX 4090 products to China and Country Group D:5 without a license. "
                "These regulatory restrictions have materially impacted our data center sales in China, requiring us "
                "to redesign products to comply with performance thresholds. "
                "Additionally, we depend heavily on independent foundries, primarily Taiwan Semiconductor Manufacturing "
                "Company Limited (TSMC), to manufacture our semiconductor wafers, and on third-party assembly and testing "
                "subcontractors. Supply chain constraints, advanced packaging shortages (such as CoWoS capacity), or "
                "geopolitical tensions in the Taiwan Strait could severely limit our ability to satisfy customer demand "
                "for Hopper and Blackwell GPU architectures."
            )
        },
        {
            "doc_id": "NVDA-2024-10K-MDA",
            "ticker": "NVDA",
            "company": "NVIDIA Corporation",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 7 - MD&A",
            "title": "NVIDIA FY2024 10-K MD&A: Data Center Revenue Growth and Financial Highlights",
            "text": (
                "Total revenue for fiscal year 2024 was $60.9 billion, an increase of 126% compared to $27.0 billion "
                "in fiscal year 2023. This growth was primarily driven by our Data Center segment, which generated "
                "$47.5 billion in revenue, up 217% year-over-year. Data Center growth was fueled by strong demand "
                "for the NVIDIA Hopper GPU architecture, including H100 Tensor Core GPUs, from large cloud service "
                "providers, consumer internet companies, and enterprise AI developers building large language models. "
                "Gaming revenue for fiscal 2024 was $10.4 billion, up 15% from the prior year, benefiting from demand "
                "for GeForce RTX 40 series GPUs based on the Ada Lovelace architecture. "
                "Gross margin for fiscal 2024 improved to 72.7% compared to 56.9% in fiscal 2023, driven by favorable "
                "product mix shifts toward high-margin Data Center computing platforms."
            )
        },
        {
            "doc_id": "NVDA-2024-Q2-EARNINGS",
            "ticker": "NVDA",
            "company": "NVIDIA Corporation",
            "doc_type": "Earnings Call",
            "fiscal_year": "2025",
            "section": "Executive Commentary",
            "title": "NVIDIA Q2 FY2025 Earnings Call: Jensen Huang on Blackwell Transition and Sovereign AI",
            "text": (
                "During the Q2 FY2025 earnings conference call, CEO Jensen Huang highlighted the transition from Hopper "
                "to the upcoming Blackwell architecture. 'Hopper demand remains exceptionally strong, and Blackwell "
                "sampling is underway with all major partners,' Huang stated. He addressed market concerns regarding "
                "Blackwell production schedules, noting that a mask change was executed to improve manufacturing yield "
                "without altering functional design. "
                "Huang also emphasized the rapid expansion of Sovereign AI investments globally, as nations in Europe, "
                "the Middle East, and Asia build sovereign AI infrastructures to preserve cultural and linguistic "
                "sovereignty. Sovereign AI and enterprise adoption are expected to contribute over $10 billion in "
                "annual revenue, diversifying demand beyond the top hyperscale cloud service providers."
            )
        },

        # =========================================================
        # APPLE (AAPL)
        # =========================================================
        {
            "doc_id": "AAPL-2024-10K-RISKS",
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 1A - Risk Factors",
            "title": "Apple FY2024 10-K Risk Factors: Regulatory Challenges and AI Competition",
            "text": (
                "Apple faces intense legal and regulatory scrutiny globally regarding the App Store ecosystem, "
                "digital markets, and antitrust compliance. In the European Union, the Digital Markets Act (DMA) "
                "has required the company to permit alternative app marketplaces, third-party payment processing, "
                "and alternative browser engines on iOS devices, which could adversely affect Services revenue and "
                "user security. "
                "Furthermore, rapid advancements in artificial intelligence and generative AI have heightened "
                "industry competition. Successfully integrating Apple Intelligence features into iOS, iPadOS, and macOS "
                "requires substantial capital expenditure on custom Apple Silicon infrastructure and cloud servers, "
                "while failure to deliver compelling AI user experiences could harm consumer demand and device upgrade "
                "cycles."
            )
        },
        {
            "doc_id": "AAPL-2024-10K-MDA",
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 7 - MD&A",
            "title": "Apple FY2024 10-K MD&A: Services Growth and iPhone Sales Performance",
            "text": (
                "For fiscal year 2024, Apple reported total net sales of $391.0 billion, up 2% compared to $383.3 billion "
                "in fiscal 2023. Products revenue totaled $294.9 billion, while Services revenue reached an all-time record "
                "of $96.2 billion, representing an increase of 13% year-over-year. "
                "Services growth was driven by increases in paid subscriptions across App Store, iCloud, Apple Music, "
                "and AppleCare, exceeding 1 billion paid subscriptions across our platform. "
                "iPhone net sales were $201.2 billion in fiscal 2024, remaining relatively flat compared to $200.6 billion "
                "in the prior year due to foreign currency headwinds and macro environment softness in Greater China. "
                "Gross margin expanded to 46.2%, supported by higher Services revenue mix and product cost efficiencies."
            )
        },
        {
            "doc_id": "AAPL-2024-Q4-EARNINGS",
            "ticker": "AAPL",
            "company": "Apple Inc.",
            "doc_type": "Earnings Call",
            "fiscal_year": "2024",
            "section": "Executive Commentary",
            "title": "Apple Q4 FY2024 Earnings Call: Tim Cook on Apple Intelligence Rollout",
            "text": (
                "In Apple's Q4 FY2024 earnings call, CEO Tim Cook detailed the phased rollout of Apple Intelligence "
                "beginning with iOS 18.1. 'We are delivering personal intelligence that is private, integrated into "
                "our core operating systems, and powered by Apple Silicon,' Cook stated. "
                "CFO Luca Maestri noted that operating cash flow for fiscal 2024 reached $118.3 billion, allowing Apple "
                "to return over $100 billion to shareholders through dividends and share repurchases. "
                "Cook highlighted that while AI server infrastructure investments will increase capital expenditures, "
                "Apple's hybrid architecture—combining on-device processing with Private Cloud Compute—optimizes both "
                "user privacy and infrastructure operating efficiency."
            )
        },

        # =========================================================
        # MICROSOFT (MSFT)
        # =========================================================
        {
            "doc_id": "MSFT-2024-10K-RISKS",
            "ticker": "MSFT",
            "company": "Microsoft Corporation",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 1A - Risk Factors",
            "title": "Microsoft FY2024 10-K Risk Factors: AI Infrastructure Costs and OpenAI Partnership",
            "text": (
                "Our strategic partnership with OpenAI is central to our artificial intelligence strategy, and we face "
                "risks associated with our dependency on OpenAI's foundational models and research. Any disruption "
                "in OpenAI's operations, leadership changes, or commercial terms could impact our product roadmap for "
                "Microsoft 365 Copilot, GitHub Copilot, and Azure OpenAI Service. "
                "In addition, building and operating AI cloud infrastructure requires unprecedented capital expenditures "
                "in data center real estate, GPUs, networking, and electrical power. If customer adoption of generative "
                "AI workloads does not grow as projected, our operating margins and return on capital could be "
                "negatively impacted. Cybersecurity threats to Azure cloud services also remain a critical risk."
            )
        },
        {
            "doc_id": "MSFT-2024-10K-MDA",
            "ticker": "MSFT",
            "company": "Microsoft Corporation",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 7 - MD&A",
            "title": "Microsoft FY2024 10-K MD&A: Azure Revenue and Intelligent Cloud Expansion",
            "text": (
                "Microsoft reported revenue of $245.1 billion for fiscal year 2024, an increase of 16% compared to "
                "fiscal 2023. Intelligent Cloud segment revenue grew 20% to $105.4 billion, driven by Azure and other "
                "cloud services growth of 30%, which benefited from increased demand for AI compute and Azure OpenAI "
                "services. "
                "Productivity and Business Processes revenue was $77.8 billion, up 13%, driven by Office 365 Commercial "
                "seat growth and adoption of Microsoft 365 Copilot among enterprise customers. "
                "Operating income increased 24% to $109.4 billion. Capital expenditures for fiscal 2024 surged to "
                "$55.7 billion, reflecting massive investments in AI data centers, GPUs, and cloud servers to support "
                "future Azure demand."
            )
        },
        {
            "doc_id": "MSFT-2025-Q1-EARNINGS",
            "ticker": "MSFT",
            "company": "Microsoft Corporation",
            "doc_type": "Earnings Call",
            "fiscal_year": "2025",
            "section": "Executive Commentary",
            "title": "Microsoft Q1 FY2025 Earnings Call: Satya Nadella on AI Run Rate and CapEx",
            "text": (
                "During Microsoft's Q1 FY2025 earnings call, CEO Satya Nadella announced that Microsoft's AI business "
                "is on track to exceed an annual revenue run rate of $10 billion next quarter—the fastest business "
                "in company history to reach this milestone. "
                "CFO Amy Hood explained that Q1 capital expenditures were $20.0 billion, with roughly half spent on "
                "long-lived assets including land and data center buildouts, and half spent on servers and GPUs. "
                "Hood emphasized that Azure supply constraints for AI compute continue to lag behind customer demand, "
                "and data center capacity expansions will gradually come online throughout the second half of the fiscal year."
            )
        },

        # =========================================================
        # TESLA (TSLA)
        # =========================================================
        {
            "doc_id": "TSLA-2024-10K-RISKS",
            "ticker": "TSLA",
            "company": "Tesla, Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 1A - Risk Factors",
            "title": "Tesla FY2024 10-K Risk Factors: EV Competition and Full Self-Driving Regulations",
            "text": (
                "We face escalating competition in the electric vehicle (EV) market from traditional automotive "
                "manufacturers and emerging Chinese EV competitors such as BYD and NIO. Price reductions and pricing "
                "pressures have impacted our automotive gross margins and average selling price (ASP). "
                "Furthermore, our long-term valuation is heavily dependent on our autonomous driving technology, "
                "including Full Self-Driving (FSD) Supervised and our planned Robotaxi / Cybercab platform. "
                "Commercial deployment of autonomous vehicles is subject to complex and evolving regulatory approvals "
                "from NHTSA and state transport authorities. Delays in achieving unsupervised autonomy or regulatory "
                "setbacks could materially harm our brand and business prospects."
            )
        },
        {
            "doc_id": "TSLA-2024-10K-MDA",
            "ticker": "TSLA",
            "company": "Tesla, Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 7 - MD&A",
            "title": "Tesla FY2024 10-K MD&A: Automotive Gross Margin and Energy Storage Growth",
            "text": (
                "For fiscal year 2024, Tesla total revenues were $96.8 billion, representing a 1% increase from $96.8 billion "
                "in fiscal 2023. Automotive revenue was $78.0 billion, declining slightly due to lower average selling prices "
                "partially offset by vehicle delivery volume of 1.79 million units. "
                "Energy Generation and Storage revenue grew significantly by 53% year-over-year to $9.2 billion, driven "
                "by record deployments of Megapack and Powerwall storage systems totaling over 15.3 GWh. "
                "Automotive gross margin excluding regulatory credits declined to 16.2% compared to 18.5% in the prior year, "
                "reflecting price reductions across Model 3 and Model Y vehicles to support global delivery volumes."
            )
        },
        {
            "doc_id": "TSLA-2024-Q3-EARNINGS",
            "ticker": "TSLA",
            "company": "Tesla, Inc.",
            "doc_type": "Earnings Call",
            "fiscal_year": "2024",
            "section": "Executive Commentary",
            "title": "Tesla Q3 2024 Earnings Call: Elon Musk on Cybercab Timeline and Megapack",
            "text": (
                "In Tesla's Q3 2024 earnings call, CEO Elon Musk discussed the unveil of the Cybercab autonomous "
                "robotaxi and the Optimus humanoid robot. Musk stated that Cybercab volume production is targeted for "
                "2026, featuring a vehicle cost below $30,000 without pedals or steering wheels. "
                "Musk highlighted that Tesla's Energy Storage business is growing faster than its automotive business, "
                "with gross margins in the energy segment reaching 30.5% in Q3. "
                "He also reaffirmed that Tesla expects 20% to 30% vehicle delivery growth in 2025, supported by lower-cost "
                "vehicle models and autonomous FSD software improvements."
            )
        },

        # =========================================================
        # ALPHABET (GOOGL)
        # =========================================================
        {
            "doc_id": "GOOGL-2024-10K-RISKS",
            "ticker": "GOOGL",
            "company": "Alphabet Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 1A - Risk Factors",
            "title": "Alphabet FY2024 10-K Risk Factors: Antitrust Regulatory Actions and AI Overviews",
            "text": (
                "Alphabet is involved in major antitrust investigations and legal proceedings in the United States and "
                "European Union. In August 2024, a U.S. federal court ruled in DOJ v. Google that Google maintained "
                "an illegal monopoly in general search services and search text advertising. Potential remedies could "
                "restrict distribution agreements with device manufacturers such as Apple and Samsung. "
                "Additionally, the integration of generative AI Overviews into Google Search presents risks regarding "
                "monetization of search advertising, computational cost per query, and potential liability or reputation "
                "harm from AI model hallucinations or inaccurate summaries presented to users."
            )
        },
        {
            "doc_id": "GOOGL-2024-10K-MDA",
            "ticker": "GOOGL",
            "company": "Alphabet Inc.",
            "doc_type": "10-K",
            "fiscal_year": "2024",
            "section": "Item 7 - MD&A",
            "title": "Alphabet FY2024 10-K MD&A: Google Cloud Profitability and Search Ad Revenue",
            "text": (
                "Alphabet consolidated revenues for fiscal year 2024 were $331.1 billion, an increase of 15% compared "
                "to $288.8 billion in 2023. Google Search and other advertising revenue grew 12% to $195.8 billion, "
                "demonstrating resilience in commercial search intent and ad formats. "
                "Google Cloud revenue increased 30% year-over-year to $43.0 billion, driven by strong enterprise "
                "demand for GCP infrastructure, Vertex AI platform, and Gemini foundational models. "
                "Significantly, Google Cloud operating income reached $6.2 billion, compared to $1.7 billion in 2023, "
                "reflecting improved operating leverage and scale across data center infrastructure."
            )
        },
        {
            "doc_id": "GOOGL-2024-Q3-EARNINGS",
            "ticker": "GOOGL",
            "company": "Alphabet Inc.",
            "doc_type": "Earnings Call",
            "fiscal_year": "2024",
            "section": "Executive Commentary",
            "title": "Alphabet Q3 2024 Earnings Call: Sundar Pichai on Gemini and Search AI Overviews",
            "text": (
                "During Alphabet's Q3 2024 earnings call, CEO Sundar Pichai highlighted that AI Overviews in Google Search "
                "are now rolling out to over 1 billion users globally. Pichai noted that user engagement and query volume "
                "increase when AI Overviews are displayed, particularly for complex information-seeking queries. "
                "He emphasized that Google has reduced the unit cost of AI Overview queries by over 70% through hardware "
                "and algorithmic optimizations on custom Tensor Processing Units (TPU v5p and Trillium). "
                "CFO Anat Ashkenazi reported that Q3 capital expenditures were $13.0 billion, primarily allocated to technical "
                "infrastructure including AI servers, TPUs, and data centers."
            )
        }
    ]

    # Save to data/sec_10k_earnings_dataset.json
    with open('/home/user/findocs-copilot/data/sec_10k_earnings_dataset.json', 'w') as f:
        json.dump(documents, f, indent=2)

    print(f"Generated {len(documents)} SEC 10-K and Earnings Call documents.")

def generate_ground_truth_qa():
    qa_pairs = [
        {
            "question_id": "q1",
            "question": "What U.S. export control rules impacted NVIDIA's GPU sales to China, and which specific GPU models were restricted?",
            "ground_truth_doc_id": "NVDA-2024-10K-RISKS",
            "ground_truth_chunk_id": "NVDA-2024-10K-RISKS_1",
            "reference_answer": "On October 17, 2023, the U.S. government issued interim final rules restricting exports of advanced computing items to China and Country Group D:5 without a license. Specifically, NVIDIA's A100, A800, H100, H800, L40, L40S, and RTX 4090 products were restricted.",
            "category": "Risk Factors",
            "ticker": "NVDA"
        },
        {
            "question_id": "q2",
            "question": "What was NVIDIA's total revenue in fiscal year 2024, and how much did the Data Center segment contribute?",
            "ground_truth_doc_id": "NVDA-2024-10K-MDA",
            "ground_truth_chunk_id": "NVDA-2024-10K-MDA_1",
            "reference_answer": "NVIDIA's total revenue for fiscal year 2024 was $60.9 billion (a 126% increase YoY). The Data Center segment contributed $47.5 billion, which was up 217% year-over-year.",
            "category": "Revenue/MD&A",
            "ticker": "NVDA"
        },
        {
            "question_id": "q3",
            "question": "What did Jensen Huang say about the transition to the Blackwell architecture and manufacturing yields?",
            "ground_truth_doc_id": "NVDA-2024-Q2-EARNINGS",
            "ground_truth_chunk_id": "NVDA-2024-Q2-EARNINGS_1",
            "reference_answer": "Jensen Huang stated that Hopper demand remains exceptionally strong and Blackwell sampling is underway with all major partners. Regarding Blackwell production schedules, a mask change was executed to improve manufacturing yield without altering functional design.",
            "category": "Earnings Strategy",
            "ticker": "NVDA"
        },
        {
            "question_id": "q4",
            "question": "How has the European Union's Digital Markets Act (DMA) affected Apple's iOS ecosystem?",
            "ground_truth_doc_id": "AAPL-2024-10K-RISKS",
            "ground_truth_chunk_id": "AAPL-2024-10K-RISKS_1",
            "reference_answer": "Under the EU Digital Markets Act (DMA), Apple has been required to permit alternative app marketplaces, third-party payment processing, and alternative browser engines on iOS devices, which could adversely affect Services revenue and user security.",
            "category": "Risk Factors",
            "ticker": "AAPL"
        },
        {
            "question_id": "q5",
            "question": "What was Apple's total Services revenue in fiscal 2024, and how many paid subscriptions did they reach?",
            "ground_truth_doc_id": "AAPL-2024-10K-MDA",
            "ground_truth_chunk_id": "AAPL-2024-10K-MDA_1",
            "reference_answer": "In fiscal 2024, Apple's Services revenue reached an all-time record of $96.2 billion (up 13% YoY), driven by over 1 billion paid subscriptions across the platform including App Store, iCloud, Apple Music, and AppleCare.",
            "category": "Revenue/MD&A",
            "ticker": "AAPL"
        },
        {
            "question_id": "q6",
            "question": "How did Tim Cook describe Apple Intelligence during the Q4 FY2024 earnings call?",
            "ground_truth_doc_id": "AAPL-2024-Q4-EARNINGS",
            "ground_truth_chunk_id": "AAPL-2024-Q4-EARNINGS_1",
            "reference_answer": "Tim Cook described Apple Intelligence as 'personal intelligence that is private, integrated into our core operating systems, and powered by Apple Silicon', with a phased rollout starting in iOS 18.1.",
            "category": "Earnings Strategy",
            "ticker": "AAPL"
        },
        {
            "question_id": "q7",
            "question": "What are the primary operational risks Microsoft faces regarding its partnership with OpenAI?",
            "ground_truth_doc_id": "MSFT-2024-10K-RISKS",
            "ground_truth_chunk_id": "MSFT-2024-10K-RISKS_1",
            "reference_answer": "Microsoft depends heavily on OpenAI's foundational models and research. Any disruption in OpenAI's operations, leadership changes, or commercial terms could negatively impact Microsoft's product roadmap for Microsoft 365 Copilot, GitHub Copilot, and Azure OpenAI Service.",
            "category": "Risk Factors",
            "ticker": "MSFT"
        },
        {
            "question_id": "q8",
            "question": "How much did Microsoft's Intelligent Cloud segment grow in fiscal 2024, and what drove Azure's revenue?",
            "ground_truth_doc_id": "MSFT-2024-10K-MDA",
            "ground_truth_chunk_id": "MSFT-2024-10K-MDA_1",
            "reference_answer": "Microsoft's Intelligent Cloud segment grew 20% to $105.4 billion in fiscal 2024, driven by 30% growth in Azure and other cloud services due to strong demand for AI compute and Azure OpenAI services.",
            "category": "Revenue/MD&A",
            "ticker": "MSFT"
        },
        {
            "question_id": "q9",
            "question": "What milestone did Satya Nadella announce regarding Microsoft's AI revenue run rate in Q1 FY2025?",
            "ground_truth_doc_id": "MSFT-2025-Q1-EARNINGS",
            "ground_truth_chunk_id": "MSFT-2025-Q1-EARNINGS_1",
            "reference_answer": "Satya Nadella announced that Microsoft's AI business is on track to exceed an annual revenue run rate of $10 billion next quarter, making it the fastest business in company history to reach that milestone.",
            "category": "Earnings Strategy",
            "ticker": "MSFT"
        },
        {
            "question_id": "q10",
            "question": "What emerging Chinese EV competitors did Tesla highlight in its FY2024 10-K risk factors?",
            "ground_truth_doc_id": "TSLA-2024-10K-RISKS",
            "ground_truth_chunk_id": "TSLA-2024-10K-RISKS_1",
            "reference_answer": "Tesla highlighted escalating competition from traditional automotive manufacturers and emerging Chinese EV competitors such as BYD and NIO, which create pricing pressures and impact automotive gross margins.",
            "category": "Risk Factors",
            "ticker": "TSLA"
        },
        {
            "question_id": "q11",
            "question": "How much did Tesla's Energy Generation and Storage revenue grow in fiscal 2024?",
            "ground_truth_doc_id": "TSLA-2024-10K-MDA",
            "ground_truth_chunk_id": "TSLA-2024-10K-MDA_1",
            "reference_answer": "Tesla's Energy Generation and Storage revenue grew 53% year-over-year to $9.2 billion in fiscal 2024, driven by record deployments of Megapack and Powerwall storage systems totaling over 15.3 GWh.",
            "category": "Revenue/MD&A",
            "ticker": "TSLA"
        },
        {
            "question_id": "q12",
            "question": "What is the target volume production year and expected cost for Tesla's Cybercab robotaxi?",
            "ground_truth_doc_id": "TSLA-2024-Q3-EARNINGS",
            "ground_truth_chunk_id": "TSLA-2024-Q3-EARNINGS_1",
            "reference_answer": "Elon Musk stated that volume production for the Cybercab autonomous robotaxi is targeted for 2026, with an expected vehicle cost below $30,000 without pedals or steering wheels.",
            "category": "Earnings Strategy",
            "ticker": "TSLA"
        },
        {
            "question_id": "q13",
            "question": "What antitrust court ruling did Alphabet face in August 2024 regarding search advertising?",
            "ground_truth_doc_id": "GOOGL-2024-10K-RISKS",
            "ground_truth_chunk_id": "GOOGL-2024-10K-RISKS_1",
            "reference_answer": "In August 2024, a U.S. federal court ruled in DOJ v. Google that Google maintained an illegal monopoly in general search services and search text advertising, which could lead to remedies restricting distribution agreements with Apple and Samsung.",
            "category": "Risk Factors",
            "ticker": "GOOGL"
        },
        {
            "question_id": "q14",
            "question": "What was Google Cloud's revenue and operating income in fiscal year 2024?",
            "ground_truth_doc_id": "GOOGL-2024-10K-MDA",
            "ground_truth_chunk_id": "GOOGL-2024-10K-MDA_1",
            "reference_answer": "In fiscal year 2024, Google Cloud revenue increased 30% year-over-year to $43.0 billion, and operating income reached $6.2 billion (up from $1.7 billion in 2023).",
            "category": "Revenue/MD&A",
            "ticker": "GOOGL"
        },
        {
            "question_id": "q15",
            "question": "How much has Alphabet reduced the unit cost of AI Overview queries in Google Search?",
            "ground_truth_doc_id": "GOOGL-2024-Q3-EARNINGS",
            "ground_truth_chunk_id": "GOOGL-2024-Q3-EARNINGS_1",
            "reference_answer": "Sundar Pichai emphasized that Google has reduced the unit cost of AI Overview queries by over 70% through hardware and algorithmic optimizations on custom TPUs (TPU v5p and Trillium).",
            "category": "Earnings Strategy",
            "ticker": "GOOGL"
        },
        {
            "question_id": "q16",
            "question": "What foundry does NVIDIA primarily rely on for manufacturing its semiconductor wafers?",
            "ground_truth_doc_id": "NVDA-2024-10K-RISKS",
            "ground_truth_chunk_id": "NVDA-2024-10K-RISKS_1",
            "reference_answer": "NVIDIA relies primarily on Taiwan Semiconductor Manufacturing Company Limited (TSMC) to manufacture its semiconductor wafers, making it vulnerable to Taiwan Strait geopolitical tensions or CoWoS packaging shortages.",
            "category": "Risk Factors",
            "ticker": "NVDA"
        },
        {
            "question_id": "q17",
            "question": "What was Apple's gross margin in fiscal 2024, and what contributed to this expansion?",
            "ground_truth_doc_id": "AAPL-2024-10K-MDA",
            "ground_truth_chunk_id": "AAPL-2024-10K-MDA_1",
            "reference_answer": "Apple's gross margin expanded to 46.2% in fiscal 2024, supported by a higher Services revenue mix and product cost efficiencies.",
            "category": "Revenue/MD&A",
            "ticker": "AAPL"
        },
        {
            "question_id": "q18",
            "question": "How much did Microsoft spend on capital expenditures in fiscal year 2024, and what was it spent on?",
            "ground_truth_doc_id": "MSFT-2024-10K-MDA",
            "ground_truth_chunk_id": "MSFT-2024-10K-MDA_1",
            "reference_answer": "Microsoft spent $55.7 billion on capital expenditures in fiscal 2024, reflecting massive investments in AI data centers, GPUs, and cloud servers to support future Azure demand.",
            "category": "Revenue/MD&A",
            "ticker": "MSFT"
        },
        {
            "question_id": "q19",
            "question": "What was Tesla's automotive gross margin excluding regulatory credits in fiscal 2024?",
            "ground_truth_doc_id": "TSLA-2024-10K-MDA",
            "ground_truth_chunk_id": "TSLA-2024-10K-MDA_1",
            "reference_answer": "Tesla's automotive gross margin excluding regulatory credits declined to 16.2% in fiscal 2024 (down from 18.5% in 2023), reflecting price reductions across Model 3 and Model Y vehicles.",
            "category": "Revenue/MD&A",
            "ticker": "TSLA"
        },
        {
            "question_id": "q20",
            "question": "What was Alphabet's consolidated total revenue in fiscal year 2024?",
            "ground_truth_doc_id": "GOOGL-2024-10K-MDA",
            "ground_truth_chunk_id": "GOOGL-2024-10K-MDA_1",
            "reference_answer": "Alphabet's consolidated revenues for fiscal year 2024 were $331.1 billion, representing a 15% increase compared to $288.8 billion in fiscal 2023.",
            "category": "Revenue/MD&A",
            "ticker": "GOOGL"
        }
    ]

    with open('/home/user/findocs-copilot/data/ground_truth_qa.json', 'w') as f:
        json.dump(qa_pairs, f, indent=2)

    print(f"Generated {len(qa_pairs)} ground truth Q&A pairs for evaluation.")

if __name__ == '__main__':
    generate_sec_dataset()
    generate_ground_truth_qa()
