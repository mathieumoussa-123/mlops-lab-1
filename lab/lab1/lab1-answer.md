# Lab 1 Answers — Git, DVC, and Data Preparation

## Question 1
Observe the files created by uv init. What do you think they contain?

In my Lab 1 project, uv init created the basic Python project structure:

- .python-version: contains the Python version used by the project.
- pyproject.toml: contains the project metadata, Python version requirement, dependencies, and project configuration.
- README.md: contains project documentation.
- Starter Python files/packages created by uv.
- uv.lock: stores the exact resolved dependency versions so the environment can be reproduced consistently.

Later, when Pillow was added for image processing, pyproject.toml was updated to include it as a dependency.

---

## Question 2
What are the files created by DVC? What do you think they are used for? Which ones should be pushed to Git?

After running:

dvc init

DVC created repository-level configuration files such as:

- .dvc/config: stores DVC repository configuration.
- .dvc/.gitignore: prevents local DVC files such as the cache, temporary files, and local configuration from being tracked by Git.
- .dvcignore: allows files or folders to be excluded from DVC scanning.

In my repository, .dvc/.gitignore prevents local files such as the DVC cache from being tracked.

The DVC configuration files should be tracked by Git, while local cache, temporary files, and secret/local configuration should not be pushed.

---

## Question 3
Where are the credentials stored? What are the options other than --global? Should the credentials be pushed to GitHub?

I configured the DagsHub credentials using the --global option. This means the credentials are stored in the user-level DVC configuration outside the Git repository.

My repository-level .dvc/config stores the non-secret DVC remote configuration, while the username and password are not stored in the repository.

Other configuration scopes include:

- Repository-level configuration in .dvc/config
- Local configuration using --local, stored in .dvc/config.local
- Global configuration using --global

Credentials should not be pushed to GitHub. They should remain in local or global configuration so that secrets are not exposed in the repository.

---

## Question 4
Take a look at the .gitignore file. Explain what happened.

After running:

dvc add data

DVC added the data directory to the Lab 1 .gitignore file.

This means Git ignores the actual dataset.

The purpose is to separate responsibilities:

- Git versions the code and the DVC pointer file.
- DVC versions the actual dataset.

This prevents thousands of image files from being stored directly in GitHub while still allowing the dataset version to be linked to a Git commit.

---

## Question 5
Do you see a .dvc file? What does it contain?

Yes. After the first:

dvc add data

DVC created:

data.dvc

At this point in the lab, only the raw Food-11 dataset had been added under data/, before food11_processed and food11_processed_mini were created.

The corresponding older version of my data.dvc file was:

outs:  
- md5: a3a457d03c51ff8b037a833440f6ad13.dir  
- size: 1188442712  
- nfiles: 16643  
- hash: md5  
- path: data

This file stores metadata describing that version of the data directory.

It contains:

- md5: the hash identifying the tracked dataset version
- size: the total size of that tracked data version
- nfiles: the number of tracked files in that version
- path: the tracked directory, which is data

The actual images are not stored inside data.dvc. The file acts as a pointer to the corresponding data version stored by DVC.

Later in the lab, after creating food11_processed and food11_processed_mini and running dvc add data again, data.dvc changed to represent the newer and larger version of the data directory.

---

## Question 6
On the GitHub main branch, is the code there? Is the data there? Is there a file that points to the data location? What about DagsHub?

Yes, the source code and project configuration are stored in Git.

The repository includes files such as:

- lab/lab1/src/food11/data.py
- lab/lab1/pyproject.toml
- lab/lab1/uv.lock
- lab/lab1/data.dvc

The actual Food-11 image files are not stored directly in Git because the data directory is ignored by Git.

The data.dvc file is stored in Git and represents the version of the dataset being tracked by DVC.

The actual data is uploaded separately using:

dvc push

and is stored in the DagsHub DVC remote.

Therefore:

Git / GitHub  
├── source code  
├── configuration  
├── .gitignore  
└── data.dvc

DVC / DagsHub  
└── actual dataset files

---

## Question 7
In a completely new temporary folder, clone the GitHub repository. Do you see the data folder? What DVC command is needed to get the data folder?

After cloning the repository with:

git clone <repository-url>

the actual dataset is not downloaded from GitHub because the data directory is managed by DVC rather than Git.

The cloned repository contains the data.dvc pointer, but the dataset itself must be restored from the DVC remote.

The command needed is:

dvc pull

DVC reads the current data.dvc file and downloads the corresponding data objects from DagsHub.

The workflow is:

git clone  
↓  
downloads code + data.dvc  
↓  
dvc pull  
↓  
reads the data.dvc pointer  
↓  
downloads the matching data from DagsHub

So git pull updates Git-tracked files, while dvc pull retrieves the actual DVC-tracked dataset.

---

## Question 8
After checking out an older Git commit and running dvc checkout, do you still see food11_processed and food11_processed_mini?

No.

The older commit contains the earlier version of data.dvc, which represented the data before the processed datasets were created.

When I checked out the older Git commit and then ran:

git checkout <old-commit-hash>  
dvc checkout

only the older local data version was restored, so I could see food11_raw, while:

food11_processed  
food11_processed_mini

were no longer present locally.

This happens because:

1. git checkout <old-commit-hash> restores the old version of data.dvc.
2. dvc checkout reads that old pointer and changes the local data directory to match it.

The newer data is not deleted from DagsHub. It remains stored remotely.

To return to the latest version, I used:

git checkout main  
dvc checkout

which restored the current dataset containing:

food11_raw  
food11_processed  
food11_processed_mini
