### CVS «mygit»
Версия: 2.0.0  
Автор: Эдуард Старков (Edward.Ekb@yandex.ru)  

#### Описание
небольшая локальная git-like система контроля версий

#### Требования
* Python версии не ниже 3.6
* Смотри requirements.txt

#### Установка
python setup.py install

#### Использование
Предполагается использование через CLI в виде единой программы, а не набора модулей.  
Справка по запуску: `mygit --help`  
Справка по отдельной команде: `mygit [команда] --help`

#### Справка
```
start work:
  init         Create an empty mygit repository

work on the current change:
  index        Add file contents to the index
  reset        Undo your changes

examine the history and state:
  status       Show the working tree status
  log          Show commit history
  print        Show content of recorded objects

grow, mark and tweak your common history:
  commit       Record changes to the repository
  branch       List, create, or delete branches
  merge        Join two or more development histories together
  checkout     Switch branches
```

##### Index
```
Add specified files to index for next commit.
Only indexed changes will be recorded by cvs

Usage examples:
  mygit index file1 file2    index changes in file1 and file2
                             Note: can take any amount of files

  mygit index dir1 dir2      index changes in every not ignored file in specified directories
                             Note: can take any amount of directories

  mygit index -a             index changes in every not ignored file in workspace
```

##### Reset
```
Reset workspace or index tree for specific files or whole workspace

Usage examples:
  mygit reset -i file1 file2 ...          if specified files was indexed, will clear them from index
                                          so it will look like they are not indexed again.
                                          Workspace won't be changed

  mygit reset -i                          clear whole index
                                          so it will look like there's no any indexed changes
                                          Workspace won't be changed

  mygit reset --hard -i file1 file2 ...   does the same that not --hard version,
                                          but then replaces specified files in workspace
                                          with their last recorded versions
                                          Note: resetting new file will delete it

  mygit reset --hard -i                   replace all indexed files with their recorded versions and clear whole index

  mygit reset                             return whole workspace to last commited condition, all changes will be lost
```

##### Status
```
Show status of all three trees: workspace, index, ignored

Usage examples:
   mygit status              show status of workspace
   mygit status --indexed    show indexed paths
   mygit status --ignored    show ignored paths
```

##### Log
```
Show commit history of current branch in classic format:
  $checksum
  $date
  $message

Usage examples:
  mygit log [-o]    key -o changes output style to "$checksum $message" format
```

##### Print
```
Show content of recorded objects

Usage examples:
  mygit print checksum1 checksum2 ...    print content of compressed object files
                                         Note: can take any amount of files
```

##### Commit
```
Record all indexed changes in cvs

Usage examples:
  mygit commit message      record indexed changes, message will be shown in log
```

##### Branch
```
Bunch of tools for branching

Usage examples:
  mygit branch -r dev              remove branch dev
                                   Note: you can't remove head/nonexistent branch

  mygit branch -l                  show all branches

  mygit branch -a expl y76ec54...  create new branch with name expl,
                                   that will point to commit y76ec54...
                                   Note: you can't create branch from nonexistent commit
                                         you can't create branch with already existent name

  mygit branch -a expl HEAD        create new branch with name expl,
                                   that will point to head commit
```

##### Merge
```
Fast-forward HEAD to another branch state (if it's possible)

Usage examples:
  mygit merge dev       merge commits from dev into HEAD
                        Note: fast-forward is possible only if HEAD commit's line
                              is subset of branch commit's line
```

##### Checkout
```
Restore workspace state so it becomes identical to another branch's recorded state

Usage examples:
  mygit checkout expl     restore expl branch workspace
                          Note: you can't checkout with indexed but uncommitted changes
                          Note: you can't checkout to current/nonexistent branch

  mygit checkout -n expl  creates new branch expl from HEAD and checkouts to it.
                          Note: it will not change your workspace or index
```
