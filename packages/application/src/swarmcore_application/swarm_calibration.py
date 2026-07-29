from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from asyncio import to_thread
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from jsonschema import Draft202012Validator

CALIBRATION_SCHEMA_VERSION = "schema://swarm-calibration/result@1"
_ISSUE_PATH = re.compile(r"^/([^/]+)/([^/]+)/issues/([1-9][0-9]*)/?$")
_PULL_URL = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pull/([1-9][0-9]*)")
_PULL_NUMBER = re.compile(r"(?:pull request|pull|pr)\s*#([1-9][0-9]*)", re.IGNORECASE)
_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "system prompt",
    "developer message",
    "忽略之前",
    "忽略以上",
    "系统提示词",
)


@dataclass(frozen=True, slots=True)
class GitHubIssueLocator:
    owner: str
    repository: str
    number: int

    @property
    def repository_key(self) -> str:
        return f"{self.owner}/{self.repository}"


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def parse_github_issue_url(value: str) -> GitHubIssueLocator:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("issueUrl must be an https://github.com issue URL")
    match = _ISSUE_PATH.fullmatch(parsed.path)
    if match is None or parsed.query or parsed.fragment:
        raise ValueError("issueUrl must match https://github.com/{owner}/{repo}/issues/{number}")
    return GitHubIssueLocator(match[1], match[2], int(match[3]))


class GitHubEvidenceClient:
    def __init__(
        self,
        *,
        token: str = "",
        base_url: str = "https://api.github.com",
        timeout_seconds: float = 20,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SwarmCore-Scheduling-Calibration/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_issue(self, issue_url: str) -> dict[str, Any]:
        locator = parse_github_issue_url(issue_url)
        response = await self._request(
            f"/repos/{locator.owner}/{locator.repository}/issues/{locator.number}"
        )
        payload = self._object(response)
        if "pull_request" in payload:
            raise ValueError("issueUrl points to a pull request, not an issue")
        return self._snapshot(
            source_type="github_issue",
            source_url=str(payload.get("html_url") or issue_url),
            payload=payload,
            response=response,
            selected={
                "repository": locator.repository_key,
                "number": locator.number,
                "id": payload.get("id"),
                "title": payload.get("title"),
                "body": payload.get("body") or "",
                "state": payload.get("state"),
                "labels": payload.get("labels") or [],
                "createdAt": payload.get("created_at"),
                "updatedAt": payload.get("updated_at"),
                "closedAt": payload.get("closed_at"),
                "closedBy": payload.get("closed_by"),
            },
        )

    async def get_discussion(self, issue_url: str) -> dict[str, Any]:
        locator = parse_github_issue_url(issue_url)
        comments_response = await self._request(
            f"/repos/{locator.owner}/{locator.repository}/issues/{locator.number}/comments",
            params={"per_page": "100"},
        )
        timeline_response = await self._request(
            f"/repos/{locator.owner}/{locator.repository}/issues/{locator.number}/timeline",
            params={"per_page": "100"},
            accept="application/vnd.github+json",
        )
        comments = self._array(comments_response)
        timeline = self._array(timeline_response)
        candidates = discover_pull_candidates(
            locator,
            [str(item.get("body") or "") for item in comments if isinstance(item, dict)],
            timeline,
        )
        payload = {
            "comments": comments,
            "timeline": timeline,
            "pullCandidates": candidates,
        }
        return {
            "sourceType": "github_discussion",
            "sourceUrl": issue_url,
            "retrievedAt": datetime.now(UTC).isoformat(),
            "etag": comments_response.headers.get("etag"),
            "contentHash": canonical_hash(payload),
            "payload": payload,
            "security": scan_untrusted_content(
                [str(item.get("body") or "") for item in comments if isinstance(item, dict)]
            ),
        }

    async def get_pull_evidence(
        self,
        issue_url: str,
        pull_candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        issue = parse_github_issue_url(issue_url)
        candidates = pull_candidates[:10]
        if not candidates:
            raise ValueError("no linked pull request candidate was found")
        failures: list[str] = []
        for candidate in candidates:
            owner = str(candidate.get("owner") or issue.owner)
            repository = str(candidate.get("repository") or issue.repository)
            number = int(candidate["number"])
            try:
                pull_response = await self._request(f"/repos/{owner}/{repository}/pulls/{number}")
                pull = self._object(pull_response)
                files_response = await self._request(
                    f"/repos/{owner}/{repository}/pulls/{number}/files",
                    params={"per_page": "100"},
                )
                files = self._array(files_response)
            except httpx.HTTPStatusError as exc:
                failures.append(f"{owner}/{repository}#{number}:{exc.response.status_code}")
                continue
            payload = {
                "repository": f"{owner}/{repository}",
                "number": number,
                "title": pull.get("title"),
                "body": pull.get("body") or "",
                "state": pull.get("state"),
                "merged": bool(pull.get("merged")),
                "mergedAt": pull.get("merged_at"),
                "mergeCommitSha": pull.get("merge_commit_sha"),
                "headSha": (pull.get("head") or {}).get("sha"),
                "baseSha": (pull.get("base") or {}).get("sha"),
                "htmlUrl": pull.get("html_url"),
                "files": files,
            }
            return self._snapshot(
                source_type="github_pull_request",
                source_url=str(pull.get("html_url")),
                payload=payload,
                response=pull_response,
                selected=payload,
            )
        raise ValueError(f"linked pull requests were unavailable: {', '.join(failures)}")

    async def _request(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        headers = {"Accept": accept} if accept else None
        response = await self._client.get(path, params=params, headers=headers)
        response.raise_for_status()
        return response

    @staticmethod
    def _object(response: httpx.Response) -> dict[str, Any]:
        value = response.json()
        if not isinstance(value, dict):
            raise ValueError("GitHub response must be an object")
        return value

    @staticmethod
    def _array(response: httpx.Response) -> list[dict[str, Any]]:
        value = response.json()
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError("GitHub response must be an array of objects")
        return value

    @staticmethod
    def _snapshot(
        *,
        source_type: str,
        source_url: str,
        payload: dict[str, Any],
        response: httpx.Response,
        selected: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "sourceType": source_type,
            "sourceUrl": source_url,
            "retrievedAt": datetime.now(UTC).isoformat(),
            "etag": response.headers.get("etag"),
            "contentHash": canonical_hash(payload),
            "payload": selected,
            "security": scan_untrusted_content(
                [str(selected.get("title") or ""), str(selected.get("body") or "")]
            ),
        }


class RepositorySandboxVerifier:
    def __init__(
        self,
        *,
        enabled: bool,
        image: str,
        docker_binary: str = "docker",
        timeout_seconds: int = 600,
        github_token: str = "",
    ) -> None:
        self._enabled = enabled
        self._image = image.strip()
        self._docker_binary = docker_binary
        self._timeout_seconds = timeout_seconds
        self._github_token = github_token

    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        del context
        repository = str(input_value["repository"])
        commit_sha = str(input_value["commitSha"]).lower()
        command = input_value.get("testCommand")
        command_items = (
            [str(item) for item in command] if isinstance(command, list) else []
        )
        if not bool(input_value.get("enabled", True)):
            return self._unverified(
                repository, commit_sha, command_items, effect_id, "SANDBOX_DISABLED"
            )
        if not self._enabled:
            return self._unverified(
                repository,
                commit_sha,
                command_items,
                effect_id,
                "SANDBOX_EXECUTOR_NOT_CONFIGURED",
            )
        self._validate(repository, commit_sha, command_items)
        archive = await self._download_archive(repository, commit_sha)
        archive_hash = hashlib.sha256(archive).hexdigest()
        execution = await to_thread(
            self._run_container,
            archive,
            commit_sha,
            command_items,
        )
        return {
            "status": "PASSED" if execution["exitCode"] == 0 else "FAILED",
            "reasonCode": None if execution["exitCode"] == 0 else "TEST_COMMAND_FAILED",
            "repository": repository,
            "commitSha": commit_sha,
            "command": command_items,
            "effectId": effect_id,
            "image": self._image,
            "archiveSha256": archive_hash,
            "exitCode": execution["exitCode"],
            "tests": _parse_test_counts(execution["output"]),
            "output": execution["output"],
            "honestStatus": True,
            "networkMode": "none",
        }

    async def _download_archive(self, repository: str, commit_sha: str) -> bytes:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SwarmCore-Scheduling-Calibration/1.0",
        }
        if self._github_token:
            headers["Authorization"] = f"Bearer {self._github_token}"
        async with httpx.AsyncClient(
            headers=headers,
            timeout=60,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                f"https://api.github.com/repos/{repository}/tarball/{commit_sha}"
            )
            response.raise_for_status()
            if len(response.content) > 100 * 1024 * 1024:
                raise ValueError("repository archive exceeds the 100 MiB sandbox limit")
            return response.content

    def _run_container(
        self,
        archive: bytes,
        commit_sha: str,
        command: list[str],
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="swarmcore-calibration-") as directory:
            archive_path = Path(directory) / "repository.tar.gz"
            archive_path.write_bytes(archive)
            process = subprocess.run(
                [
                    self._docker_binary,
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--read-only",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--pids-limit",
                    "256",
                    "--memory",
                    "1g",
                    "--cpus",
                    "1",
                    "--tmpfs",
                    "/tmp:rw,noexec,nosuid,size=256m",
                    "--tmpfs",
                    "/workspace:rw,nosuid,size=1g",
                    "--mount",
                    f"type=bind,src={archive_path},dst=/input/repository.tar.gz,readonly",
                    self._image,
                    "--archive",
                    "/input/repository.tar.gz",
                    "--commit-sha",
                    commit_sha,
                    "--",
                    *command,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                shell=False,
            )
        output = "\n".join(
            item.strip() for item in (process.stdout, process.stderr) if item.strip()
        )
        return {"exitCode": process.returncode, "output": output[-20_000:]}

    def _validate(self, repository: str, commit_sha: str, command: list[str]) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("repository must be a GitHub owner/repository identifier")
        if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            raise ValueError("commitSha must be a full lowercase Git SHA")
        if not command or len(command) > 32 or any(len(item) > 512 for item in command):
            raise ValueError("testCommand must contain 1 to 32 bounded arguments")
        if "@sha256:" not in self._image:
            raise ValueError("sandbox image must be digest pinned")
        if self._timeout_seconds < 1 or self._timeout_seconds > 3600:
            raise ValueError("sandbox timeout must be between 1 and 3600 seconds")

    @staticmethod
    def _unverified(
        repository: str,
        commit_sha: str,
        command: list[str],
        effect_id: str,
        reason_code: str,
    ) -> dict[str, Any]:
        return {
            "status": "UNVERIFIED",
            "reasonCode": reason_code,
            "repository": repository,
            "commitSha": commit_sha,
            "command": command,
            "effectId": effect_id,
            "exitCode": None,
            "tests": {"passed": 0, "failed": 0, "skipped": 0},
            "honestStatus": True,
        }


def _parse_test_counts(output: str) -> dict[str, int]:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for key in counts:
        matches = re.findall(rf"([0-9]+)\s+{key}\b", output, re.IGNORECASE)
        if matches:
            counts[key] = int(matches[-1])
    return counts


def discover_pull_candidates(
    issue: GitHubIssueLocator,
    comment_bodies: list[str],
    timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for event in timeline:
        source = event.get("source")
        source_issue = source.get("issue") if isinstance(source, dict) else None
        pull = source_issue.get("pull_request") if isinstance(source_issue, dict) else None
        if isinstance(source_issue, dict) and isinstance(pull, dict):
            url = str(pull.get("html_url") or "")
            match = _PULL_URL.search(url)
            if match:
                candidates.append(
                    {
                        "owner": match[1],
                        "repository": match[2],
                        "number": int(match[3]),
                        "source": "timeline",
                    }
                )
    for body in comment_bodies:
        for match in _PULL_URL.finditer(body):
            candidates.append(
                {
                    "owner": match[1],
                    "repository": match[2],
                    "number": int(match[3]),
                    "source": "comment_url",
                }
            )
        for match in _PULL_NUMBER.finditer(body):
            candidates.append(
                {
                    "owner": issue.owner,
                    "repository": issue.repository,
                    "number": int(match[1]),
                    "source": "comment_reference",
                }
            )
    unique: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in candidates:
        key = (str(item["owner"]), str(item["repository"]), int(item["number"]))
        unique.setdefault(key, item)
    return list(unique.values())


def scan_untrusted_content(values: list[str]) -> dict[str, Any]:
    matches = sorted(
        {
            marker
            for value in values
            for marker in _INJECTION_MARKERS
            if marker in value.casefold()
        }
    )
    return {
        "untrusted": True,
        "promptInjectionSuspected": bool(matches),
        "markers": matches,
        "handling": "DATA_ONLY",
    }


def freeze_evidence(
    issue: dict[str, Any],
    discussion: dict[str, Any],
    pull_request: dict[str, Any],
) -> dict[str, Any]:
    snapshots = [issue, discussion, pull_request]
    required = {"sourceType", "sourceUrl", "retrievedAt", "contentHash", "payload"}
    for snapshot in snapshots:
        missing = required - snapshot.keys()
        if missing:
            raise ValueError(f"evidence snapshot is missing: {', '.join(sorted(missing))}")
    merge_sha = str(pull_request["payload"].get("mergeCommitSha") or "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", merge_sha):
        raise ValueError("pull request evidence must contain a full merge commit SHA")
    index = [
        {
            "evidenceId": f"ev-{position:03d}",
            "sourceType": snapshot["sourceType"],
            "sourceUrl": snapshot["sourceUrl"],
            "retrievedAt": snapshot["retrievedAt"],
            "etag": snapshot.get("etag"),
            "contentHash": snapshot["contentHash"],
            "commitSha": merge_sha if snapshot["sourceType"] == "github_pull_request" else None,
            "security": dict(snapshot.get("security") or {}),
        }
        for position, snapshot in enumerate(snapshots, start=1)
    ]
    frozen = {
        "repository": issue["payload"]["repository"],
        "issueNumber": issue["payload"]["number"],
        "mergeCommitSha": merge_sha.lower(),
        "snapshots": snapshots,
        "evidenceIndex": index,
    }
    return {**frozen, "evidenceManifestHash": canonical_hash(frozen)}


def build_route_decision(
    recommendation: dict[str, Any],
    *,
    primary_ready: bool,
    standby_ready: bool,
) -> dict[str, Any]:
    requested = str(recommendation.get("recommendedRoute") or "PRIMARY")
    if primary_ready and requested != "STANDBY":
        selected = "PRIMARY"
        reasons = list(recommendation.get("reasonCodes") or [])
    elif standby_ready:
        selected = "STANDBY"
        reasons = [*list(recommendation.get("reasonCodes") or []), "PRIMARY_NOT_READY"]
    else:
        selected = "HUMAN"
        reasons = [*list(recommendation.get("reasonCodes") or []), "NO_AGENT_ROUTE_READY"]
    return {
        "recommendedRoute": requested,
        "selectedRoute": selected,
        "reasonCodes": sorted(set(str(item) for item in reasons)),
        "primaryAgentRef": "agent://calibration/primary-diagnostician@1",
        "selectedAgentRef": (
            "agent://calibration/standby-diagnostician@1"
            if selected == "STANDBY"
            else "agent://calibration/primary-diagnostician@1"
            if selected == "PRIMARY"
            else None
        ),
        "runtimeAuthoritative": True,
    }


def verify_result_schema(result: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(result),
        key=lambda item: list(item.path),
    )
    return {
        "valid": not errors,
        "errors": [
            {
                "path": ".".join(str(part) for part in error.path),
                "message": error.message,
            }
            for error in errors
        ],
    }


def score_quality(
    *,
    diagnosis: dict[str, Any],
    schema_valid: bool,
    evidence_ids: set[str],
    sandbox: dict[str, Any],
    judge: dict[str, Any],
    acceptance_criteria: list[str],
) -> dict[str, Any]:
    claims = diagnosis.get("claims")
    claim_items = claims if isinstance(claims, list) else []
    material = [
        item for item in claim_items if isinstance(item, dict) and item.get("material", True)
    ]
    supported = [
        item
        for item in material
        if set(str(ref) for ref in item.get("evidenceRefs", [])) & evidence_ids
    ]
    coverage = len(supported) / len(material) if material else 0.0
    mappings = diagnosis.get("acceptanceMapping")
    mapped = mappings if isinstance(mappings, list) else []
    mapped_criteria = {str(item.get("criterion")) for item in mapped if isinstance(item, dict)}
    acceptance_coverage = (
        sum(item in mapped_criteria for item in acceptance_criteria) / len(acceptance_criteria)
        if acceptance_criteria
        else 1.0
    )
    sandbox_status = str(sandbox.get("status") or "UNVERIFIED")
    evidence_consistent = bool(judge.get("evidenceConsistent", False))
    components = {
        "schema": 20.0 if schema_valid else 0.0,
        "sourceCompleteness": 15.0 if len(evidence_ids) >= 3 else 5.0 * len(evidence_ids),
        "evidenceCoverage": round(25.0 * coverage, 2),
        "evidenceConsistency": 15.0 if evidence_consistent else 0.0,
        "sandboxVerification": 15.0 if sandbox_status == "PASSED" else 0.0,
        "acceptanceCoverage": round(10.0 * acceptance_coverage, 2),
    }
    hard_failures: list[str] = []
    if not schema_valid:
        hard_failures.append("SCHEMA_INVALID")
    if len(evidence_ids) < 3:
        hard_failures.append("SOURCE_INCOMPLETE")
    if coverage < 0.9:
        hard_failures.append("EVIDENCE_COVERAGE_LOW")
    if not evidence_consistent:
        hard_failures.append("EVIDENCE_CONFLICT")
    if acceptance_coverage < 1:
        hard_failures.append("ACCEPTANCE_UNMAPPED")
    score = round(sum(components.values()), 2)
    if sandbox_status != "PASSED":
        score = min(score, 79.0)
        hard_failures.append("RUNTIME_UNVERIFIED")
    decision = "PASS" if score >= 85 and not hard_failures else "REVIEW_REQUIRED"
    return {
        "decision": decision,
        "score": score,
        "threshold": 85,
        "components": components,
        "evidenceCoverage": round(coverage, 4),
        "acceptanceCoverage": round(acceptance_coverage, 4),
        "hardFailures": sorted(set(hard_failures)),
        "sandboxStatus": sandbox_status,
    }


def finalize_calibration_result(
    *,
    payload: dict[str, Any],
    evidence: dict[str, Any],
    route: dict[str, Any],
    diagnosis: dict[str, Any],
    quality: dict[str, Any],
    sandbox: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route = dict(route)
    if fallback and fallback.get("used"):
        route["selectedRoute"] = "STANDBY"
        route["selectedAgentRef"] = "agent://calibration/standby-diagnostician@1"
        route["reasonCodes"] = sorted(
            {
                *(str(item) for item in route.get("reasonCodes", [])),
                "PRIMARY_EXECUTION_FAILED",
            }
        )
        route["fallback"] = {
            "used": True,
            "fromAgentRef": "agent://calibration/primary-diagnostician@1",
            "toAgentRef": "agent://calibration/standby-diagnostician@1",
            "triggerCode": "PRIMARY_EXECUTION_FAILED",
            "error": str(fallback.get("reason") or ""),
        }
    approved = bool((approvals or {}).get("approved"))
    quality_passed = quality.get("decision") == "PASS"
    selected_route = str(route.get("selectedRoute") or "HUMAN")
    status = (
        "COMPLETED_DEGRADED"
        if quality_passed and selected_route == "STANDBY"
        else "COMPLETED"
        if quality_passed
        else "COMPLETED_DEGRADED"
        if approved
        else "REVIEW_REQUIRED"
    )
    result = {
        "schemaVersion": CALIBRATION_SCHEMA_VERSION,
        "status": status,
        "issue": {
            "url": payload["issueUrl"],
            "objective": payload["objective"],
            "repository": evidence["repository"],
            "number": evidence["issueNumber"],
            "commitSha": evidence["mergeCommitSha"],
        },
        "route": route,
        "diagnosis": diagnosis,
        "quality": quality,
        "sandbox": sandbox,
        "evidence": evidence["evidenceIndex"],
        "provenance": {
            "evidenceManifestHash": evidence["evidenceManifestHash"],
            "generatedAt": datetime.now(UTC).isoformat(),
            "externalWritePerformed": False,
        },
    }
    return {**result, "resultHash": canonical_hash(result)}


def calibration_report_lines(result: dict[str, Any]) -> list[str]:
    issue = result["issue"]
    quality = result["quality"]
    diagnosis = result["diagnosis"]
    return [
        "智能体调度校准报告",
        f"业务状态: {result['status']}",
        f"问题: {issue['repository']}#{issue['number']}",
        f"固定提交: {issue['commitSha']}",
        f"目标: {issue['objective']}",
        f"质量得分: {quality['score']} / 100",
        f"执行路由: {result['route']['selectedRoute']}",
        f"运行验证: {result['sandbox']['status']}",
        "",
        "问题摘要",
        str(diagnosis.get("summary") or ""),
        "",
        "根因",
        str(diagnosis.get("rootCause") or ""),
        "",
        "修复机制",
        str(diagnosis.get("fixMechanism") or ""),
    ]


__all__ = [
    "CALIBRATION_SCHEMA_VERSION",
    "GitHubEvidenceClient",
    "GitHubIssueLocator",
    "RepositorySandboxVerifier",
    "build_route_decision",
    "calibration_report_lines",
    "canonical_hash",
    "discover_pull_candidates",
    "finalize_calibration_result",
    "freeze_evidence",
    "parse_github_issue_url",
    "scan_untrusted_content",
    "score_quality",
    "verify_result_schema",
]
