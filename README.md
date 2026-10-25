## Intended for myself in an alternate universe: THE BUCK!

### Assumptions
This program assumes the following:
- User is an annual pass holder, and is able to enter the park at 5pm before the haunted houses open at 7pm, and has one quick queue use for the houses
- User wants to see the monkeys upon entry
- User's significant other wants to ride Iron Gwazi first, but is open to seeing the wait-time penalty of doing so before deciding
- User intends to visit all haunted houses before riding rides during the period that haunted houses are open

### Important Program Specifications
- The 15-integer arrays represent attraction wait times in 30-minute intervals from 5:30-12:30
- The first 3 integers in haunted house arrays should be set to -1, denoting that they are closed
- For filling in wait times, it is recommended to use the PROJECTED wait times for the SPECIFIC DATE which you plan on attending
- I recommend using queue-times.com, though they do not always have projected times available
- If the projected wait times are not available, you can use ChatGPT to roughly estimate
- Wait times should be in minutes
- Quick Queue wait times are extremely hard to find, but 5 accross the board can generally be used
- In my experience, projected house wait times are typically accurate
- Ride wait times are typically shorter than expected prior to 7pm, and longer than expected after 7pm
- Chances are, you will be able to ride more rides before 7pm than expected
- The BUFFER variable denotes how much leeway in minutes you want to give yourself between getting on one attraction and arriving in the line for the next

### Instructions For Use
- Install Python 3.10+ and Git
- Clone the repository
- Edit the BUFFER variable and Queue arrays as necissary
- Run the program

### Outputs
- Two schedules: One globally optimized and one where Iron Gwazi is ridden first -- Each schedule contains: The attraction, expected time to enter the line, expected wait time, a note for which house to use the quick queue on
- The wait-time penalty for doing Iron Gwazi first
