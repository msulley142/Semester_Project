## User Stories

As a **user**, I want to **create a skill/habit** so that I can **monitor and log my progress**.
**Acceptance Criteria**
1. The user can select between creating a skill or a habit.
2. The user can enter the name,short description,goal, and start/end date.
3. When the Add button is clicked, the user will recieve a confirmation message. (Skill/habbit added successfully) 


As a **user**, I want to **track bad habbits** so that I **can make note of relaspes, triggers,  and urges**. 
**Acceptance Criteria** 
1. The user clicks the feather symbol on the dashboard or the Journal Entry button on the Discipline Builder webpage.
2. The user selected the habit name, specidied the type of log (progress,Lapse, urge, or reflection).
3. The user submit the journal entry which is saved and  automatically.
4. The users data appears on the Progress tracker page with updated streaks or lapse counts
5. The user will reiceve a confirmation messge that the entry was logged. 

As a **user**, I want to **write journal entries** so that I can **reflect on expirences**.
**Acceptance Criteria**
1. The user clicks the feather symbol on the dashboard or the Journal Entry button on the Discipline Builder webpage.
2. The user write a reflection  and clicks submit.
3. The user recieves a confimation message that they entry was saved successfully. 
4. The Journal entry becomes viewable inside of the skill or habit when it is selected. It is also avalible in the Journal Page. 
5. Journal Entries are stored and sorted by date.

As a **user**, I want to **earn points and badges** for obtaining streaks, and loging progress. 
**Acceptance Crtiteria**
1. The Web application will reward the user with XP and badges when they complete a specific milestone. ( Streaks and Quest Completion)
2. A notification appears when the user recieves XP or a badge. 
3. The user can view recent rawards in the Dashboard reward section.
4. A full list of rewards is viewable on the Rewards webpage. 

As a **user**, I want to **chat with other users** so that we can **dicuss our  struggles, progress and exchange advice**. 
**Acceptance  Criteria** 
1. The user can access community forums on the Community webpage.
2. The user can start a new thread or comment by clicking the + button.
3. The post form includes a textbox and submit button.
4. After submitting the post, a success messasge will confirm that the post was uploaded.
5. The post will display in the selected forum category.

As a **user**, I want to **join and or form a group of users who skills and habits are similar** to **increase community, raise morale**. 
1. The user can search for public groups based on a prefered skill or habit.
2. The user can request to join a group or create a group with a name and description.
3. Members can view groups progress, post updates, react to others acheivement. 
4. A success message will confirm when the user joins a group or creates thier own.


As a **Moderator**, I want to be able to **Monitor chats and forums** to ensure **community guidlines are being followed**
**Acceptance Criteria**
1. The moderator can view all public and repoted posts.
2. They can flag and delete post that violate community guidelines.
3. The Moderator can suspend or ban user who continue to break the rules.

## User Mis-Stories 

As a **Malicious User**, I **post offensive content**, so that i can make other users upset.
**Mitgation Criteria**
1. Use moderators to monitors chats.
2. The user can report the post or chat by clicking the report button. The report is then sent to the moderator or an automatic system for anaylsis. 
3. The users can use the block button on users who make them uncomfortable. 

As a **Malicious User**, I want to **spam forums and chats**, so that i can **slow down degrade the service for other users.**
**Mitgation Criteria**
1. Post rate limting function that only allows a certian number of post per hour/day.
2. Captcha or email to verify users when they sign up or login. 
3. A rate limit on repeated actions. 

As a **Hacker**, I want to **gain elevated priviledges** so that I can gain access to user information and or degrade user experience.
**Mitgation Criteria**
1. Use Role base access control for the admin, coach, and moderators endpoints.
2. Create an audit trail for actions performed by admin.
3. Enforce a strong password policy.
4. Disable accounts that repeated failed login attempts. 


As a **Malicious User**, I want to send repeated API request, so that i can increase my XP and gain badges.
**Mitgation Criteria**
1. XP and Tokens can validated on the server-side.
2. Rate limiting on loging progress to prevent spam submissions.


## Diagrams 

### Mockups
![alt text](<Screenshot 2025-11-01 143113.png>)
![alt text](<Screenshot 2025-11-01 143137.png>)
![alt text](<Screenshot 2025-11-01 143248.png>) 
![alt text](<Screenshot 2025-11-01 143215.png>) 
![alt text](<Screenshot 2025-11-01 143232.png>)

### C4 models 
![alt text](<Screenshot 2025-11-01 143749.png>)
![alt text](<Screenshot 2025-11-01 143803.png>)
![alt text](<Screenshot 2025-11-01 143813.png>)