def score_results(results, subtasks):
    groups = []
    score = sum(r["score"] for r in results if not r.get("subtask_key"))
    for group in subtasks:
        cases = [r for r in results if r.get("subtask_key") == group["subtask_key"]]
        passed = bool(cases) and all(r["status"] == "AC" for r in cases)
        awarded = group["score"] if passed else 0
        score += awarded
        groups.append({"subtask_key": group["subtask_key"], "status": "AC" if passed else "WA",
                       "score": awarded, "max_score": group["score"]})
    status = next((r["status"] for r in results if r["status"] != "AC"), "AC")
    return status, score, groups
