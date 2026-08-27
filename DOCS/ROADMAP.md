# ShellArc: Animation Production Pipeline Server Framework

> ### **Development Branch**: `dev_2027`

---

### Project Overview
ShellArc is an animation production pipeline server framework designed to integrate and streamline production workflows. 
This roadmap and agenda target development on the **`dev_2027`** branch. Each task is annotated with **[Urgency / Scale (1-5)]** to visualize priorities.

---

### Development Agenda & Tasks

#### 1. Code Quality
- Implementation of dependency injection [Urgency: 5 / Scale: 4] *SOLVED
- Implementation of comprehensive unit tests [Urgency: 5 / Scale: 4]
- Implementation of a comprehensive dummy-operatable UI [Urgency: 4 / Scale: 3]
- Establish CI/CD test automation [Urgency: 5 / Scale: 3]
- Improve docstrings [Urgency: 4 / Scale: 1]
- Refactor codes with low readability and excessively lengthy scripts [Urgency: 4 / Scale: 3]

#### 2. Math and Data Science
- Embed ShellArc Railgun Architecture Model into the ShellArc core module [Urgency: 4 / Scale: 5]
  - (https://github.com/shinonome-MiDUki/Shell_Arc_Railgun_scheduler)

#### 3. Cloud and Infrastructure
- Implement auto-backup on AWS Deep Glacier [Urgency: 3 / Scale: 2]
- Allow safe HTTPS communication with desktop apps and local programs [Urgency: 3 / Scale: 4]
- Revise Docker configurations for improving development iteration [Urgency: 4 / Scale: 1]

#### 4. Format and Data Structure
- Migrate from subprocess commands to PyGit2 for better performance and higher flexibility [Urgency: 2 / Scale: 4]
- Standardize project description data format for projects under ShellArc's management [Urgency: 3 / Scale: 5]

#### 5. Desktop Applications
- Incorporate Shell DELTA into the ShellArc eco-system [Urgency: 4 / Scale: 4]
  - (https://github.com/shinonome-MiDUki/Shell_DELTA)
- Extend compositing features of Shell DELTA and improve GLSL support [Urgency: 4 / Scale: 2]
- Implement Python scripting for Shell DELTA [Urgency: 3 / Scale: 3]
- Improve UI of the ShellArc Desktop app [Urgency: 4 / Scale: 2]
- Extend project management features and project progress visualization [Urgency: 4 / Scale: 5]

#### 6. Expression and Intepreter
- Enhance the embedded SAPYC expression language for more flexible and safe operations without directly touching the backend [Urgency: 4 / Scale: 4]

#### 7. Graphics and Media
- Improve GPU usage and efficiency of the NUDEC codec format [Urgency: 3 / Scale: 4]
- Improve synchronization with surrounding audio systems [Urgency: 4 / Scale: 3]
- Establish CI workflow for `.nuanim` cloud rendering [Urgency: 3 / Scale: 2]

#### 8. AI and Machine Learning
- Establish an automation workflow for RAG updates upon updates [Urgency: 4 / Scale: 1]
- Establish an auto-coloring system via Runpod and ComfyUI [Urgency: 3 / Scale: 3]
- Improve skill sheets for agent-driven ShellArc extension and customization developments [Urgency: 3 / Scale: 1]

#### 9. Automation Server
- Improve Item Action auto-scheduling server to production level [Urgency: 3 / Scale: 2]

#### 10. Minor Features
- Implement customisable entry point expression [Urgency: 3 / Scale : 1]
