#!/bin/bash
set -e

# Get the null commit SHA
NULL_SHA=0000000000000000000000000000000000000000

# Create a temporary branch from the null commit
git checkout -b temp $NULL_SHA

# Read the tree of commit 74aa581
git read-tree 74aa581^{tree}

# Remove the .env file from the index
git update-index --remove .env

# Write the tree and get its SHA
NEW_TREE_SHA=$(git write-tree)

# Create a commit from this tree with the same message as 74aa581 but without the .env file
# We'll use the commit message from 74aa581
COMMIT_MSG=$(git show 74aa581 --format=%B)

# Create the new root commit
NEW_ROOT_SHA=$(echo "$COMMIT_MSG" | git commit-tree $NEW_TREE_SHA -p $NULL_SHA)

# Now, cherry-pick the UI update commit (342f28a) on top of the new root
git checkout -b new_main $NEW_ROOT_SHA
git cherry-pick 342f28a

# Update the main branch to point to new_main
git checkout main
git reset --hard new_main

# Clean up temporary branches
git branch -D temp new_main

# Force push
git push --force-with-lease origin main