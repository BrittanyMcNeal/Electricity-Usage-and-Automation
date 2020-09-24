# Electric Bill Optimization

Knowing your energy usage can help you save money. This is especially true if you are on a special energy plan in which you get a discount if you use a certain amount. In this case, my energy plan offers an incentive where if I use between 1000 and 1500 kWh in a monthly billing cycle, I save $60. 

![Infuse Enegy plan 2020 snapshot](/assets/Infuse%20Enegy%20plan%202020%20snapshot.png)

[SmartMeterTexas](https://www.smartmetertexas.com/quickrefguides) offers a free API to pull your home electricity usage. Using [Ankit Kumar Choudhary's](https://github.com/ankitkchoudhary/electricity-usage-monitoring) handy interface with the API, I pulled daily usage for my billing cycle. Unfortunately billing cycle dates are not available from the API, so they must be extracted to a CSV from [CenterPoint's PDF schedule](https://www.centerpointenergy.com/en-us/Documents/2020-Meter-Read-Schedule-for-Cycles-1-21-Non-IDR.pdf).

![Centerpoint Energy Schedule 2020](/assets/Centerpoint%20Energy%20Schedule%202020.png)


I used Pandas to join my energy usage with the billing schedule and print some summary information about my billing cycle and usage trend.

> Cycle Start: 2020-09-03 00:00:00
> Cycle End: 2020-10-05 00:00:00
> Today: 2020-09-17 20:53:19
> Days Passed: 14
> Days Remaining: 17
> Usage so far: 537.2
> Usage per day so far: 36
> Target usage for the rest of the cycle: 27

I also graphed my energy expenditure per billing cycle. The pink line is my actual usage and the blue is my target usage.

![Energy_Usage_Sept_Oct](https://i.imgur.com/Jf0HMWN.png)


So this is good, we are liking it but I still want more. I want to be messaged a reminder like any millenial would. To make my dreams a reality, I made an Twilio account and used Twilio's API to send a reminder to my phone to use more or less energy.

![Twilio](/assets/Twilio.jpg)

I had the messaging system working but to use it, I would have to go log into my computer and manually run the program which is time consuming. To level up my project, I used a Rasberry Pi to automate my reminders. I first connected my Pi to my computer using VNC. I then used Cron to schedule my program to run and send me a message every Monday, Wendesday, and Friday at 1:00 pm. 

>0 13 * * 1,3,5 cd /home/pi/Desktop/Electricity-Usage-Optimization && python3 runner.py >> script.log 2>&1




