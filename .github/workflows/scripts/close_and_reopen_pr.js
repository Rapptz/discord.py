module.exports = (async function ({github, context}) {
    const pr_number = process.env.PR_NUMBER;
    const pr_operation = process.env.PR_OPERATION;

    if (!['created', 'updated'].includes(pr_operation)) {
        console.log('PR was not created as there were no changes.')
        return;
    }

    // Close the PR
    github.issues.update({
        issue_number: pr_number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        state: 'closed'
    });

    // Wait a moment for GitHub to process it...
    await new Promise(r => setTimeout(r, 2000));

    // Then reopen the PR so it runs CI
    github.issues.update({
        issue_number: pr_number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        state: 'open'
    });
})
