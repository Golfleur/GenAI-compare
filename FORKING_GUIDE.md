# Guide: Creating a Fork from Golfleur/GenAI-compare to Laverydebilly/l3ia-genai-compare

This guide explains how to create a new repository (Laverydebilly/l3ia-genai-compare) based on the Golfleur/GenAI-compare repository.

## Option 1: Fork via GitHub UI (Recommended for most users)

### Step 1: Fork the Repository

1. Go to https://github.com/Golfleur/GenAI-compare
2. Click the "Fork" button in the top-right corner
3. In the "Owner" dropdown, select "Laverydebilly" (you must have access to this account/organization)
4. Change the repository name to "l3ia-genai-compare"
5. Optionally add a description
6. Click "Create fork"

### Step 2: Clone Your Fork Locally

```bash
git clone https://github.com/Laverydebilly/l3ia-genai-compare.git
cd l3ia-genai-compare
```

### Step 3: Add Upstream Remote (to keep in sync with original)

```bash
git remote add upstream https://github.com/Golfleur/GenAI-compare.git
git remote -v
```

### Step 4: Keep Your Fork Updated

```bash
# Fetch changes from the original repository
git fetch upstream

# Merge changes into your main branch
git checkout main
git merge upstream/main

# Push updates to your fork
git push origin main
```

## Option 2: Mirror the Repository (For complete independence)

If you want a complete copy without maintaining a fork relationship:

### Step 1: Create a Bare Clone

```bash
git clone --bare https://github.com/Golfleur/GenAI-compare.git
cd GenAI-compare.git
```

### Step 2: Create New Repository on GitHub

1. Go to GitHub and create a new repository named "l3ia-genai-compare" under the "Laverydebilly" account
2. **Do not** initialize it with README, .gitignore, or license

### Step 3: Mirror Push to New Repository

```bash
git push --mirror https://github.com/Laverydebilly/l3ia-genai-compare.git
```

### Step 4: Clean Up and Clone Your New Repository

```bash
cd ..
rm -rf GenAI-compare.git
git clone https://github.com/Laverydebilly/l3ia-genai-compare.git
cd l3ia-genai-compare
```

## Option 3: Import via GitHub UI

1. Go to https://github.com/new/import
2. Enter the old repository URL: `https://github.com/Golfleur/GenAI-compare`
3. Choose "Laverydebilly" as the owner
4. Set repository name as "l3ia-genai-compare"
5. Choose public or private
6. Click "Begin import"

## Working with Your New Repository

### Create a New Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Your commit message"

# Push to your repository
git push origin feature/your-feature-name
```

### Keep Your Fork Synced (if using Option 1)

Set up a scheduled sync or manually sync periodically:

```bash
# Sync main branch
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Rebase your feature branch on updated main
git checkout feature/your-feature-name
git rebase main
```

## Important Notes

1. **Permissions Required**: You need to have:
   - Access to the Laverydebilly GitHub account or organization
   - Permission to create new repositories under that account

2. **Fork vs Mirror**:
   - **Fork**: Maintains a connection to the original repository, easier to sync updates
   - **Mirror**: Complete independent copy, no connection to original

3. **License Considerations**: 
   - This repository uses the LICENSE file in the root directory
   - Ensure you comply with the license terms when forking/mirroring

4. **Repository Visibility**:
   - Forks of public repositories are public by default
   - Mirrors can be private if you have a paid GitHub account

## Troubleshooting

### "Repository already exists"
If the repository name is already taken, choose a different name or delete the existing repository first.

### "Permission denied"
Ensure you have the necessary permissions for the Laverydebilly account.

### "Fatal: could not read from remote repository"
Check your authentication (SSH keys or personal access token) is properly configured.

## Next Steps

After setting up your repository:

1. Update the README.md to reflect the new repository location
2. Update any documentation that references the old repository
3. Set up branch protection rules if needed
4. Configure GitHub Actions/workflows if they exist
5. Invite collaborators to the new repository
