Setting up some git things
===
How to handin &c. in the INF3200 course
----
This guide has been adapted from the CS171 course at harvard, see https://github.com/CS171/2015-cs171-homework

Git
---

In this course, we will be using a tool called git to track changes to our code. We'll also be using Github, an online tool for hosting git repositories.

First, let's configure git: open a shell. Run the following.

```
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL ADDRESS"
```

`cd` to the directory you want put your homework in (e.g., your Documents folder).


Run the following:

```
git clone https://github.com/uit-inf-3200/mandatory -o mandatory
```

Then `cd` into the newly created `mandatory/` directory.  You can change the directory name if you want.


Create a new repository on the Github website following the `inf3200-lastname-firstname` naming convention. **Use all lowercase for your repository name. It is important that your repository be named exactly as above so that we can access it for grading.**

Ensure your new repository is private and don't click the option to "Initialize the repository with a README".

Unless you know what you're doing, select HTTPS.

![Setting up your Github repository](images/https.png?raw=true)

Run the two commands described on GitHub under the heading "Push an existing repository from the command line", highlighted in red below.

![Setting up your Github repository](images/commands.png?raw=true)

On GitHub, go to the repository settings and navigate to the Collaborators page. Add [`assignman3200`](https://github.com/assignman3200) as a collaborator to your private repository.

Now your homework repository is all set!

### Committing

While working on homework assignments, periodically run the following:

```
git add -A
git commit -m "Describe your changes"
git push
```

The `git commit` operation takes snapshot of your code at that point in time — a snapshot is called a "commit" in Git parlance. You can revert to a previous commit at any time.

The `git push` operation pushes your local commits to the remote repository. It is important that you push your changes or others will not be able to see them.

You should do this frequently: as often as you have an incremental, standalone improvement.

### Submitting your homework

We will automatically copy your repository after each homework deadline. **You do not need to do anything else to submit your work (but make sure that you have pushed the latest version of your homework).** We will count the time of your last commit to the Github repository as your submission time.


### Getting new homework assignments

When we release a new assignment we will simply add it to the [mandatory github repository](https://github.com/uit-inf-3200/mandatory/).

To get the latest homework assignments and potential updates or corrections to the assignment, run the following.

```
git pull mandatory master
```

Make sure to have all your changes committed before you do that.


### For the super curious
What we've done is to set up a local git repo with two remote repos: the inf3200/mandatory repo, which you only get to pull assignment text & precode and such from, and your own github repo, which is where you push your code to. The `assignman3200` collaborator you have to add is so that we can easily pull your code+report in for assessment after handin.
