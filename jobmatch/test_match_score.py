# jobmatch/test_match_score.py
from jobmatch.retrieve_score import retrieve_match_result

# SAMPLE IDs (change based on DB)
USER_ID = 1
JOB_ID = 1

score, matched, missing = retrieve_match_result(USER_ID, JOB_ID)

print("Match Score:", score)
print("Matched Skills:", matched)   
print("Missing Skills:", missing)
