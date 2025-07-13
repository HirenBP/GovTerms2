import time
from extractor import GlossaryExtractor

FAILED_ENTRIES = [
    ("Australian Broadcasting Corporation", "https://www.transparency.gov.au/publications/communications-and-the-arts/australian-broadcasting-corporation/australian-broadcasting-corporation-annual-report-2023-24/abbreviations-list"),
    ("Australian National Audit Office", "https://www.transparency.gov.au/publications/prime-minister-and-cabinet/australian-national-audit-office/australian-national-audit-office-annual-report-2023-24/abbreviations-and-acronyms"),
    ("Attorney-General's Department", "https://www.transparency.gov.au/publications/attorney-general-s/attorney-generals-department/attorney-general-s-department-annual-report-2023-24/glossary-of-abbreviations-and-acronyms"),
    ("Commonwealth Superannuation Corporation (CSC)", "https://www.transparency.gov.au/publications/finance/commonwealth-superannuation-corporation-csc/commonwealth-superannuation-corporation-annual-report-2023-24/10.-glossary"),
    ("Department of Foreign Affairs and Trade", "https://www.transparency.gov.au/publications/foreign-affairs-and-trade/department-of-foreign-affairs-and-trade/department-of-foreign-affairs-and-trade-annual-report-2023-24/abbreviations-and-acronyms"),
    ("Aged Care Quality and Safety Commission", "https://www.transparency.gov.au/publications/health/aged-care-quality-and-safety-commission/aged-care-quality-and-safety-commission-annual-report-2023-2024/glossary-"),
    ("National Emergency Management Agency", "https://www.transparency.gov.au/publications/home-affairs/national-emergency-management-agency/national-emergency-management-agency-annual-report-2023-24/appendix-2%3A-acronyms-and-abbreviations/acronyms-and-abbreviations"),
    ("National Indigenous Australians Agency", "https://www.transparency.gov.au/publications/prime-minister-and-cabinet/national-indigenous-australians-agency/national-indigenous-australians-agency-annual-report-2023-24/section-6---glossary-and-indexes/glossary"),
    ("Australian Fisheries Management Authority", "https://www.transparency.gov.au/publications/agriculture/australian-fisheries-management-authority/australian-fisheries-management-authority-annual-report-2023-24/references/glossary"),
    ("Australian Criminal Intelligence Commission", "https://www.transparency.gov.au/publications/attorney-general-s/australian-criminal-intelligence-commission/australian-criminal-intelligence-commission-annual-report-2023-24/section-5%3A-appendices-and-references/glossary"),
    ("Australian Centre for International Agricultural Research (ACIAR)", "https://www.transparency.gov.au/publications/foreign-affairs-and-trade/australian-centre-for-international-agricultural-research-aciar/australian-centre-for-international-agricultural-research-annual-report-2023-24/part-6-reference-material/abbreviations-and-acronyms"),
    ("Australian Competition and Consumer Commission (ACCC)", "https://www.transparency.gov.au/publications/treasury/australian-competition-and-consumer-commission-accc/accc-and-aer-annual-report-2023-24/part-6---appendixes/glossary-and-abbreviations"),
    ("Australian Security Intelligence Organisation", "https://www.transparency.gov.au/publications/home-affairs/australian-security-intelligence-organisation/asio-annual-report-2023-24/preliminaries/abbreviations-and-short-forms"),
    ("Australian Security Intelligence Organisation", "https://www.transparency.gov.au/publications/home-affairs/australian-security-intelligence-organisation/asio-annual-report-2023-24/preliminaries/glossary"),
    ("Australian Research Council", "https://www.transparency.gov.au/publications/education/australian-research-council/australian-research-council-annual-report-2023-24/part-6%3A-reference-material/glossary"),
    ("Australian Submarine Agency", "https://www.transparency.gov.au/publications/defence/australian-submarine-agency/australian-submarine-agency-annual-report-2023-24/chapter-5%3A-appendices/appendix-f%3A-glossary-of-abbreviations-and-acronyms"),
    ("Commonwealth Scientific and Industrial Research Organisation", "https://www.transparency.gov.au/publications/industry-innovation-and-science/commonwealth-scientific-and-industrial-research-organisation/commonwealth-scientific-and-industrial-research-organisation-annual-report-2023-24/part-6%3A-appendices-and-indexes-/glossary"),
    ("Coal Mining Industry (Long Service Leave Funding) Corporation", "https://www.transparency.gov.au/publications/attorney-general-s/coal-mining-industry-long-service-leave-funding-corporation/coal-mining-industry-long-service-leave-funding-corporation-annual-report-2023-24/-part-5.-appendices/glossary-and-acronyms"),
    ("Department of Social Services", "https://www.transparency.gov.au/publications/social-services/department-of-social-services/department-of-social-services-2023-24-annual-report/part-6---appendices-and-index/appendix-g-glossary-of-abbreviations-and-acronyms"),
    ("Department of Veterans' Affairs", "https://www.transparency.gov.au/publications/veterans-affairs/department-of-veterans-affairs/dva-annual-report-2023-24/08-aids-to-access/acronyms-and-abbreviations"),
    ("Department of Parliamentary Services", "https://www.transparency.gov.au/publications/parliamentary-departments-not-a-portfolio/department-of-parliamentary-services/department-of-parliamentary-services-annual-report-2023-2024/part-9%3A-reference-material/acronyms-and-abbreviations"),
    ("Future Fund Management Agency", "https://www.transparency.gov.au/publications/finance/future-fund-management-agency/future-fund-management-agency-annual-report-2023-24/08-references-and-index/glossary-of-abbreviations-and-acronyms"),
    ("Independent Health and Aged Care Pricing Authority", "https://www.transparency.gov.au/publications/health-and-aged-care/independent-health-and-aged-care-pricing-authority/independent-health-and-aged-care-pricing-authority-annual-report-2023-24/appendices/appendix-b-%E2%80%94-acronyms-and-abbreviations"),
    ("Great Barrier Reef Marine Park Authority", "https://www.transparency.gov.au/publications/agriculture-water-and-the-environment/great-barrier-reef-marine-park-authority/great-barrier-reef-marine-park-authority-annual-report-2023-24/6.-appendices/acronyms-and-abbreviations"),
    ("Independent Health and Aged Care Pricing Authority", "https://www.transparency.gov.au/publications/health-and-aged-care/independent-health-and-aged-care-pricing-authority/independent-health-and-aged-care-pricing-authority-annual-report-2023-24/appendices/appendix-c-%E2%80%94-glossary"),
    ("Murray-Darling Basin Authority", "https://www.transparency.gov.au/publications/agriculture/murray-darling-basin-authority/murray-darling-basin-authority-annual-report-2023-24/appendices/glossary"),
    ("National Anti-Corruption Commission", "https://www.transparency.gov.au/publications/attorney-general-s/national-anti-corruption-commission/national-anti-corruption-commission-annual-report-2023-24/aides-to-access/acronyms-and-abbreviations"),
    ("National Anti-Corruption Commission", "https://www.transparency.gov.au/publications/attorney-general-s/national-anti-corruption-commission/national-anti-corruption-commission-annual-report-2023-24/aides-to-access/glossary-of-data-terms"),
    ("National Gallery of Australia", "https://www.transparency.gov.au/publications/communications-and-the-arts/national-gallery-of-australia/national-gallery-of-australia-annual-report-2023-24/part-6%3A-appendices/abbreviations-and-acronyms"),
    ("National Health Funding Body (NHFB)", "https://www.transparency.gov.au/publications/health/national-health-funding-body-nhfb/national-health-funding-body-annual-report-2023-24/part-5%3A-reference-information/glossary"),
    ("National Transport Commission", "https://www.transparency.gov.au/publications/infrastructure-transport-cities-and-regional-development/national-transport-commission/national-transport-commission-annual-report-2023-24/appendices/appendix-e%3A-glossary-and-acronyms"),
    ("Office of the Fair Work Ombudsman", "https://www.transparency.gov.au/publications/attorney-general-s/office-of-the-fair-work-ombudsman/office-of-the-fair-work-ombudsman-2023-24-annual-report/part-5---reference-material/abbreviations-and-acronyms"),
    ("Office of the Fair Work Ombudsman", "https://www.transparency.gov.au/publications/attorney-general-s/office-of-the-fair-work-ombudsman/office-of-the-fair-work-ombudsman-2023-24-annual-report/part-5---reference-material/glossary"),
    ("National Mental Health Commission", "https://www.transparency.gov.au/publications/health/national-mental-health-commission/national-mental-health-commission-annual-report-2023-24/navigation-aids/acronyms"),
    ("National Mental Health Commission", "https://www.transparency.gov.au/publications/health/national-mental-health-commission/national-mental-health-commission-annual-report-2023-24/navigation-aids/glossary"),
    ("Rural Industries Research and Development Corporation", "https://www.transparency.gov.au/publications/agriculture/rural-industries-research-and-development-corporation/agrifutures-australia-annual-report-2023-2024/appendices/appendix-4%3A-glossary"),
    ("Parliamentary Workplace Support Service", "https://www.transparency.gov.au/publications/finance/parliamentary-workplace-support-service/parliamentary-workplace-support-service-annual-report-2023-24/part-5.-appendices/appendix-g--abbreviations-and-acronyms"),
    ("Tourism Australia", "https://www.transparency.gov.au/publications/foreign-affairs-and-trade/tourism-australia/tourism-australia-annual-report-2023-24/7.-appendix/7.5-abbreviations-and-acronyms"),
    ("Royal Australian Mint", "https://www.transparency.gov.au/publications/treasury/royal-australian-mint/annual-report-royal-australian-mint-2023-2024/09-indices/glossary"),
    ("Royal Australian Mint", "https://www.transparency.gov.au/publications/treasury/royal-australian-mint/annual-report-royal-australian-mint-2023-2024/05-annual-performance-statements/key-definitions"),
]

def main():
    extractor = GlossaryExtractor()
    log_lines = []
    results = []
    start_time = time.time()
    for entity, url in FAILED_ENTRIES:
        try:
            data = extractor.extract_from_url(url)
            glossary = data.get("glossary", {})
            num_terms = len(glossary)
            results.append((entity, url, glossary, num_terms))
            log_lines.append(f"[SUCCESS] {entity} | {url} | {num_terms} terms")
        except Exception as e:
            results.append((entity, url, {}, 0))
            log_lines.append(f"[ERROR] {entity} | {url} | {str(e)}")
    elapsed = time.time() - start_time
    log_lines.append(f"[INFO] Extraction finished. Elapsed time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

    with open(r"data/output/failed_glossary_retry_results.txt", "w", encoding="utf-8") as f:
        for entity, url, glossary, num_terms in results:
            f.write(f"Entity: {entity} | Number of Terms: {num_terms}\n")
            f.write(f"Url: {url}\n")
            for term, definition in glossary.items():
                f.write(f"{term}: {definition}\n")
            f.write("\n")

    with open(r"data/output/failed_glossary_retry_log.txt", "w", encoding="utf-8") as f:
        for line in log_lines:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
