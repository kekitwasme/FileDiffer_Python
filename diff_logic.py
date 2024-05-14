import json
from pygit2 import Repository, discover_repository

class GenerateDiff:
    """
    Handles the generation of diffs for merges (and commits)
    Requires the compared directories to be repos.
    """
    def __init__(self, repo_path):
        self.repo_path = discover_repository(repo_path)
        if self.repo_path is None:
            raise ValueError("Repository not found at provided path")
        self.repo = Repository(self.repo_path)
        self.diff_data = {}

    def output_merge_diff_json(self, target_branch, source_branch=None):
        self._merge_diff(target_branch, source_branch)
        return json.dumps(self.diff_data, indent=4)

    def output_commit_diff_json(self, source_commit, target_commit):
        pass

    def _merge_diff(self, target_branch, source_branch=None):
        """
        Compares diff between merges. Compares the diff between the branch and the 
        common ancestor of both branches 
        """
        if source_branch is None:
            source_branch = self._get_default_branch()
        
        #Find common ancestor. Need to address scenario where files are similar but not forked 
        source_commit = self.repo.revparse_single(source_branch)
        target_commit = self.repo.revparse_single(target_branch)
        base_commit = self.repo.merge_base(source_commit.id, target_commit.id)
        base_commit_obj = self.repo.get(base_commit)

        diff = self.repo.diff(base_commit_obj, source_commit)
        
        self.diff_data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "base_commit_id": str(base_commit),
            "diff_summary": {
                "total_files_changed": diff.stats.files_changed,
                "total_insertions": diff.stats.insertions,
                "total_deletions": diff.stats.deletions
            }
        }
        self._generate_diff_structure(diff)

    def _commit_diff(self, source_commit, target_commit):
        pass

    def _generate_diff_structure(self, diff):
        self.diff_data["changes"] = []
        for patch in diff:
            file_change = {
                "file_path": patch.delta.new_file.path,
                "added_lines": patch.line_stats[1],
                "deleted_lines": patch.line_stats[2],
                "hunks": []
            }
            for hunk in patch.hunks:
                hunk_details = {
                    "header": hunk.header,
                    "lines": []
                }
                for line in hunk.lines:
                    line_details = {
                        "content": line.content.strip(),
                        "type": line.origin,
                        "new_lineno": line.new_lineno,
                        "old_lineno": line.old_lineno
                    }
                    hunk_details["lines"].append(line_details)
                file_change["hunks"].append(hunk_details)
            self.diff_data["changes"].append(file_change)

    def _get_default_branch(self):
        # Return the HEAD as a symbolic reference to the default branch
        return self.repo.head.shorthand
