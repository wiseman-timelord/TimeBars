# TimeLoop
### Status
Working. Further development possible.

##
### Description
TimeLoop is a versatile timer application that allows users to select predefined timer durations ranging from 1 minute to 2 hours, it is intended as 1 better than the logical, maximum and minimum, times for a break period. It's designed for users who need to manage their time effectively while having a break from tasks, through a, simple and interactive, method. At the end of the timer is a "Timer Over!" screen with a, fitting and non-annoying, 5 bleep alarm sound played once. Optimally one would have this on the second screen while playing "Fallout 4" or whatever is your thing.

### Feautes
- **Customizable Timer Durations:** Offers a selection of predefined timer durations ranging from 1 minute to 2 hours, allowing users to choose the most suitable length for their tasks.
- **Real-time Timer Progress Display:** Updates the console in real-time with a progress bar, elapsed time, and remaining time, providing visual feedback during the countdown.
- **Audible and Visual, Notification:** Plays a sound and displays a message when the timer concludes, ensuring users are promptly notified.
- **Low Resource Usage:** The update timer is 5 seconds during the timer phase, so as to use minimal processing resources.

### Preview
- The Main Menu...
```
=================( TimeLoop )=================


             1. 2 Hours Timer

             2. 1 Hour Timer

             3. 30 Minutes Timer

             4. 15 Minutes Timer

             5. 10 Minutes Timer

             6. 5 Minutes Timer

             7. 1 Minute Timer


----------------------------------------------
Select, Options = 1-7, Exit = X:


```
- The 1 Minute Timer (test timer)...
```
=================( TimeLoop )=================

Timer Running...





   Elapsed: 00:00:30 - Remaining: 00:00:29

  [████████████████████                    ]







----------------------------------------------



```
- Event "Timer Over"...
```
=================( TimeLoop )=================








                 Timer Over!








----------------------------------------------
Select, Repeat = R, Menu = M, Exit = X:

```

##
### Usage 
Usage Guide for TimeLoop:
1. Run the Batch launcher "TimeLoop.Bat" to run the program.
2. Enter the number corresponding to your desired timer duration (1-7) or 'X' to exit.
3.  Monitor the real-time progress through the displayed progress bar and time information.
4. Listen for the audible alert and observe the "Timer Over!" message, then choose 'R' to repeat, 'M' for the main menu, or 'X' to exit.

### Notation
- Use a target entry like this `cmd.exe /c "D:\ParentFolders\TimeLoop\TimeLoop.Bat"` in your shortcut if you want to put it on the taskbar for easy access.

##
### Development
- Re-brand to "TimeBar" before release. Affected: Code referencess, ascii art, display configuration, filenames, documentation, batch code.
- Fit display to size of main menu.

##
### Disclaimer
This software is subject to the terms in License.Txt, covering usage, distribution, and modifications. For full details on your rights and obligations, refer to License.Txt.
