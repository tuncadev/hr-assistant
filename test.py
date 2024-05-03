import json

import pandas as pd
from tools.db_connect import DBConnect
from tools.getvacancies import GetVacData

with DBConnect() as db:
    applicant_key = "gIrmFO8mrl"
    content = """Education:
Online courses for QA in Techmission (October 2022 - February 2023)
Mukachevo State Institute: Economics and Management (2006-2011)

Experience:
Supervisor (head of the sales team) at Ukrprominvest Mukachevo
- Planned, organized, motivated, and controlled a sales team of 5 people
- Achieved planned indicators by 105% or more
- Managed quantitative and qualitative distribution on the territory
- Developed marketing programs to promote the product and displace competitors

I am a responsible, punctual, self-motivated specialist who excels in team environments to achieve results. I am eager to contribute my skills and experience to your company. Thank you for considering my application.

"""
    vacancy = db.insert_into_reports(applicant_key=applicant_key, report_table="first_analysis", content=content)
