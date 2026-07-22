# How to setup parrot.py to work with talon
updated: 2026-07-21

Parrot.py integration enables you to make noises such as `pops`, `clicks`, and `hiss` sounds which trigger Talon actions.  Any sound which is not part of normal speech can be used, even non-human sounds such as a bell can work.

Prereq: requires the `beta` tier of [Talon Voice](https://talonvoice.com/) which is a paid tier via patreon at [lunixbochs](https://www.patreon.com/join/lunixbochs).

If you have trouble, the best place for help is on slack `talonvoice.slack.com` in the `#ext-parrot` channel.

Helpful video tutorials are found on youtube.  These videos are slightly outdated because the current parrot.py has a newer display.  (Thanks Pokey Rule, I would have never figured this out without your videos getting me started on the right track!)
- [Use noises to control your computer part I: Parrot.py and Talon tutorial](https://www.youtube.com/watch?v=2j90vhzRoT8)
- [Use noises to control your computer part II: Parrot.py and Talon tutorial](https://www.youtube.com/watch?v=IVV6P-M9qYc)

The basic steps are:
1. setup parrot.py
1. record samples of noises, background, speech, etc.
1. have parrot.py learn from the samples and create a `model.pkl`
1. add the parrot integration to talon
1. add your model
1. setup talon commands
1. tune the thresholds

## setup parrot.py

This step will install Parrot.py on your local machine. Parrot.py is used to record audio data and train a machine learning model to recognize (e.g. categorize) audio.

Setup parrot.py [according to the instructions on parrot's github](https://github.com/chaosparrot/parrot.py/blob/master/docs/INSTALLATION.md)

- tip: create a virtual python environment to isolate the python and libraries. [video](https://youtu.be/2j90vhzRoT8?feature=shared&t=111)
    1. clone parrot.py the repo
    1. cd into the parrot.py repo folder
    1. run `python3 -py 3.12 -m venv .venv` to create the virtual environment
    1. run `source .venv/bin/activate` to activate the virtual environment
    1. then continue the install.
    - note: anytime you restart your terminal/shell to use parrot.py in the future, be sure to active the environment again.
    - note: python version 3.12 required at time of writing

Once its setup you should be able to run `python settings.py` and get the Parrot.PY main menu:
```text
Welcome to Parrot.PY setup!
----------------------------
Enter one of the buttons below and press enter to start
 - [R] for recording
 - [V] for resegmenting audio files with different thresholds
       and converting files into different formats
 - [L] for learning the data
 - [C] for combining multiple models into one model
 - [A] for analyzing the performance of the models
 - [X] for exiting setup
```

## record samples

In this step you will use parrot.py to capture recordings of the noises you want to recognize. Also you will capture exmples of sounds you dont want to recognize such as speech and background noises.  These recordings are used in later steps to train a model that can recognize these sounds.

A good reference for noises to consider is found at [@GlossikaPhonics](https://www.youtube.com/@GlossikaPhonics/playlists)

Noises you want to recognize must not match phonics in your native speech! Otherwise they will trigger when you speak normal words.

Before starting, I recommend you perform a mic check by opening a tool such as Audacity and recording some sample of yourself.  Make sure the mic is working and the sound level is loud enough without clipping. Your noise and speech should stand out from the background noise and sound floor.

To record your sounds follow these steps:
1. start parrot.py (run `python settings.py`)
1. pick `R` from the menu `[R] for recording`
1. give your sound a name.  note, this is the name you will later use in Talon.
1. next you will see a list of microphones, pick your microphone.  its possible to record on multiple mics at the same time.
1. record yourself making the sound A LOT OF TIMES.  You want to have enough samples to fill ~1min - 1min 30sec of samples.  Be prepared for this to take some time.  When I was recording a short "click" sound it took me 15 minutes of clicking and it got very tiring. the recording screen looks like this:
```text
Record keyboard controls:
[SPACE] is used to pause and resume the recording session
[BACKSPACE] or [-] removes the last 3 seconds of the recording
[ESC] stops the current recording

.-----------------------------------------------.
| Listening for:                      00:54,630 |
| Sound Quality:                      Excellent |
| dBFS:                                     -45 |
| Δ:                                          5 |
|-----------------------------------------------|
| Est. values for thresholding                  |
|-----------------------------------------------|
| Noise floor (dBFS):                       -50 |
| SNR:                                       31 |
|-----------------------------------------------|
| random                                        |
| Recorded:                           00:23,055 |
| Data Quantity:               Sufficient (26%) |
| type:                              CONTINUOUS |
| dBFS treshold:                         -39.85 |
'-----------------------------------------------'
```
- You want:
    - `Sound Quality` to be `Excellent`
    - `Recorded` to increase until you reach the length you want.  the `Data Quantity` gives you an indication of how much is needed (usually 60 to 90 seconds).  You can record more, but you get diminishing returns.  Its best to make all your recordings about the same `Recorded` length.
6. press Esc when you are finished.
    - the recordings will go into the `data/recordings` sub folder.  You can listen to them or check them in Audacity to see what was recorded.
1. repeat recording with other noises you wish to recognize
1. repeat recording to make a recording of background sounds you dont want to trigger talon actions.  this can be a single recording that contains a lot of different background sounds from your office. Such as keyboard and mouse clicks, your breathing, chair noises, drawers opening and closing, electronics that beep, clothing rustling, etc.
1. repeat recording for your speech. this will help parrot to avoid recognizing your own speech as noises.  just make a single recording of yourself talking just like you would normally do in your office. be sure to include words that make plosive sounds such as b,d,g,k,p,t sounds that make a sudden release of air and can sound like a pop on the mic.b

Side note: The instructions for [recording: Checking the quality of the detection ( Optional )](https://github.com/chaosparrot/parrot.py/blob/master/docs/RECORDING.md#checking-the-quality-of-the-detection--optional-) show how to see what was recognized. We've found the `*comparison.wav` file is usually 2x the length of the recording. In Audacity you can make it match by using `effect -> pitch and tempo -> change speed -> speed multiplier = 2` on the comparison file. Be careful that you DO NOT SAVE these changes overwriting the original file.

When you complete this step you will have multiple recordings under Parrot.py's `data/recordings` sub folder. Each folder is the named after the category that parrot will recognize the matching sounds.

## train the model

1. from the parrot.py main menu pick `L` for ` - [L] for learning the data`
1. answer `Y` to the question `Use the current audio settings for this model? Y/N ( Empty is yes )`
1. at `Insert the model name ( empty is '' )` give your model a name. tip: add a date or timestamp to the name
1. next it prompts:
```text
Type the algorithm that you wish to use for recognition
- [R] Random Forest ( SKLEARN - For quick verification )
- [A] Audio Net ( Neural net in Pytorch - Required by TalonVoice )
- [M] Multi Layer Perceptron ( Neural net in SKLEARN )
- [X] Exit the learning
```
1. pick `A` for `Audio Net` which is required for Talon
1. at `How many nets do you wish to train at the same time? ( Default is 3 )` enter a number. PokeyRule says 5 works fine for him.  If you find your resulting model doesn't do well, you can retry with a higher number.
1. next it will ask `Selecting categories to train on... ( [Y]es / [N]o / [S]kip )` and iterate over all the recordings found in the `data` sub folder.  Answer `y` for each one you want in your model.  Include your background and speech recordings/categories as well so the model can classify stuff that you dont want to recognize.
1. wait ... it will take awhile for parrot to train and make the model.
    - the warning `UserWarning: n_fft=2048 is too large for input signal of length=480` can be ignored
    - the error `using oversampling: ZeroDivisionError: division by zero` may crash the learning.  I was able to get past this by changing th code in `lib/load_data.py` (around line 173 in the function sample_data_from_label) so that it ignores the error and keeps going:
    ```python
    if label in sample_strategies:
        strategy = sample_strategies[label]["strategy"]
        truncate_after = sample_strategies[label]["truncate_after"]
        if strategy == "oversample":
            if sample_strategies[label]["total_size"] == 0:
                print( f"Loading in {label} using oversampling: ZeroDivisionError: division by zero" )
            else:
                print( f"Loading in {label} using oversampling: +" + str(abs(round(sample_strategies[label]["total_loaded"] / sample_strategies[label]["total_size"] * 100) - 100)) + "%" )
        elif strategy == "undersample":
            print( f"Loading in {label} using undersampling: -" + str(abs(round(sample_strategies[label]["total_loaded"] / sample_strategies[label]["total_size"] * 100) - 100)) + "%" )
        elif strategy == "background":
            print( f"Loading in {label} by sampling from other labels" )

            # Early return for background loading as we do that during other loading sequences
            return data
        else:
            print( f"Loading in {label}" )
    ```

When finished, there will be a model file in the `data/models` sub folder.

## test the model

1. in parrot.py root directory, copy docs/examples/mode_tutorial_a.py to data/code
1. in parrot.py data/code/config.py, set DEFAULT_CLF_FILE to name of model without .pkl
1. in parrot.py data/code/config.py, set STARTING_MODE to mode_tutorial_a
1. python3 play.py -t

## add parrot integration to talon

1. go to the `#beta` channel on slack `talonvoice.slack.com` workspace, in the Pinned messages you will find a download link for `parrot_example.zip`.  Download to a temporary location on your computer and extract its contents.  This will contain:
```text
.
├── parrot
│  ├── model.pkl
│  └── patterns.json
└── user
   ├── parrot.talon
   └── parrot_integration.py
```
1. make a new directory `parrot` under your talon user home. if you use the [talonhub/community](https://github.com/talonhub/community) (formally `knausj_talon`), then its recommend you create the `parrot` folder under community's `plugin` folder.  for example `~/.talon/user/talon/knausj_talon/plugin/parrot` on mac.
1. copy the `parrot.talon` and `parrot_integration.py` into the `parrot` folder you just created.

## add your model

This step add the `model.pkl` and `patterns.json` where Talon expects to load it. You will customize the `patterns.json` to your sounds.

1. make a directory 'parrot' _directly_ under your talon home. for example `~/.talon/parrot` on mac.
    - note: if you really want to put your model somewhere else, you can edit the `parrot_integration.py` and change the folder it loads from.
1. in your `parrot.py` you can find your trained model under `data/models`, its the `*.pkl` (pickle) file. copy your model into the `parrot` folder you just created under talon home.
1. the logic in `parrot_integration.py` is looking for the file named `model.pkl`. if your file has a different name, either rename it, or create a symbolic link with the `model.pkl` name.
1. copy the `patterns.json` file from `parrot_example.zip` to your talon home parrot folder, the same folder where you put the model.
1. edit the `patterns.json` file.
    - rename the top level keys as you wish, this is the name you will use later in `parrot.talon` to setup commands
        - change the value of the `sounds` to the name of the noise (category) you wish to match. if you forgot the name, look at the folder names in parrot.py's `data/recordings` folder for the folder name used when training your model.
        - adjust the `threshold` as needed. (more on this later)
        - adjust the `throttle`. the values are floats such that 0.1 = 100 miliseconds, 0.12 = 120 miliseconds.
            - throttle the current sound to avoid triggering multiple times on a single noise.  for example, if it take you 200 ms to make a "cluck" sound, then set the "cluck" throttle to 0.2 or larger.
            - throttle any similar sounds that you wish to avoid triggering at the same time. you only need to throttle other sounds listed in patterns.json.
    - remove extra keys that you didn't train or dont want to trigger in Talon.

Note: Talon should automatically pick changes to `patterns.json`. If it doesn't, you may need to restart Talon after making changes.

## setup talon commands

1. edit the `parrot.talon` file. it will contain examples like...
    ```talon
    parrot(cluck):
        print("cluck")
    ```
    - note: there is no context header, these commands will run anytime.
    - modify the `parrot(cluck)` line to instead have the names from your `patterns.json` file (the top level key in the json).
    - recommended: start with simply `print("name of sound")` and/or `app.notify("name of sound")` to see when the sound is triggered.  you can use this for awhile to see how well the triggering is working.
        - to see the `print` output, open talon's log (say `talon open log`).
        - the `app.notify` will popup a notification when the sound is triggered. (Note: when Talon's log has focus, the app.notify does not show)

When completed, Talon should perform the action when you make the matching sound. If it doesn't trigger, or triggers when it shouldn't then the following section will help you tune parrot.

## tune the thresholds

This step adjusts parrot's settings to help recognize sounds correctly.

In the `patterns.json` file, you can adjust the `threshold` to adjust the power (e.g. loudness) and probability (e.g. confidence in the match) required to trigger parrot.

1. open the talon repl (say `talon open rebel`)
1. in the repl enter `events.tail()`
1. now make the sounds and you should see messages in the repl like `action core.run_talon_script(ResourceContext("user.talon.knausj_talon.plugin.parrot.parrot.talon"), TalonScript(code='print("cluck")'), ParrotFrame(classes=(background-03-19-2024=0.003, silence=0.005, cluck=0.992, ...), power=231.8, f0=1193.8, f1=749.5, f2=2973.7))`
    - there are two value to watch: `power=???` and `name-of-sound=?.???` (cluck in this example) these are the power and probability scores needed that triggered the action.
1. make the sound a lot of times and observe the power and probability values
    - if you get incorrect triggering, adjust the corresponding values in your `patterns.json`. e.g. increase/decrease power or probability.
    - if it too often triggers on similar low power sounds, then increase the power required.
    - if it too often triggers on similar sounds, then increase the probability required.
    - if it doesn't trigger, try decreasing the power or probability.

When finished, the sound should trigger only when you intended to trigger it.
