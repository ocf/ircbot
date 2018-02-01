"""Print information about GitHub links."""
import github3


def register(bot):
    bot.listen(r'https?://github.com/([^/]+)/([^/]+?)/?(?:[ #]|$)', project_info)
    bot.listen(r'https?://github.com/([^/]+)/([^/]+)/issues/([0-9]+)/?\b', issue_info)
    bot.listen(r'https?://github.com/([^/]+)/([^/]+)/pull/([0-9]+)/?\b', pr_info)


def project_info(bot, msg):
    """Show GitHub project information."""
    user, repo_name = msg.match.groups()

    github = github3.GitHub()
    repo = github.repository(user, repo_name)

    if repo is not None:
        msg.respond(
            '\x0303{user}/{repo}\x03 | \x0308{stars} stars\x03 | \x0314{description}\x03'.format(
                user=user,
                repo=repo_name,
                stars=repo.stargazers,
                description=repo.description,
            ),
            ping=False,
        )


def issue_info(bot, msg):
    """Show GitHub project issue information."""
    user, repo_name, issue_num = msg.match.groups()

    github = github3.GitHub()
    repo = github.repository(user, repo_name)

    if repo is not None:
        issue = repo.issue(int(issue_num))
        if issue is not None:
            msg.respond(
                '\x0314Issue #{num}: {title}\x03 (\x0308{state}\x03, filed by \x0302{user}\x03)'.format(
                    num=issue_num,
                    title=issue.title,
                    state=issue.state,
                    user=issue.user.login,
                ),
                ping=False,
            )


def pr_info(bot, msg):
    """Show GitHub project pull request information."""
    user, repo_name, pr_num = msg.match.groups()

    github = github3.GitHub()
    repo = github.repository(user, repo_name)

    if repo is not None:
        pr = repo.pull_request(int(pr_num))
        if pr is not None:
            msg.respond(
                '\x0314PR #{num}: {title}\x03 (\x0308{state}\x03, submitted by \x0302{user}\x03)'.format(
                    num=pr_num,
                    title=pr.title,
                    state=pr.state,
                    user=pr.user.login,
                ),
                ping=False,
            )
