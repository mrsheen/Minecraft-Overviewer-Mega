============================
Minecraft Overviewer -- Mega
============================
Based upon Andrew 'brownan' Brown's Minecraft Overviewer

Modified heavily to suit large maps (500k+ chunks)

For brownan's package:

http://github.com/brownan/Minecraft-Overviewer

I suggest running brownan's package before using mine, to get a feel for the
application, how it works, the directory structure needed, and the type of
ouput it produces. Once you have everything working (on a small map), try moving
to my package, but be sure to read and understand the readme, as there are major
differences. I assume a fairly detailed knowledge of how vanilla Overviewer
works, and will skip over lots of the details covered by the vanilla package.

(To contact me, send me a message on Github, or submit an issue to my repo)

Features
========

* Specialised for maps over 500k+ chunks, which take many hours to render
  using vanilla overviewer

Initial Idea
============

Below is the initial idea I had for this fork.

-- start text wall --

I've been chewing on an idea about a changing the application's model, which will make a big difference for maps over 500k. Core premise is to make it a continuous process, which maintains a queue of chunks to render.

-- Warning: text wall below --

I've found incremental rendering of anything under ~3000 chunks is completed in near-realtime when running on hardware equivalent of a 500k+ map (ie, sufficient CPU, disk IO and memory). My idea of a queue is to continually pump a list of updated chunks to a single instance of the application. We force a save-all every fifteen minutes, and will use the rsync output as the list of updated chunks.

The application can sort the queue by any number of metrics, my first thought is to keep a 'priority' queue of often-used chunks. So if a chunk appears in the standard queue more than say 4 times (ie, is being updated every fifteen minutes for an hour), set it as a high priority. The app continuously takes sets of 1000 chunks from the high priority queue, and renders them (rendering surrounding chunks as needed for occlusion). When a priority chunk is rendered, a flag is set for that chunk so it can't be prioritzed again for a full threshold cycle (ie 4 more times). When the priority queue is emptied, it starts grabbing chunks from the standard queue. When the standard queue is emptied (ie, the render process catches up to all live changes), it start picking chunks from the world directory that have not appeared in the queues.

Couple of notes:

* process does not need to actually be run continuously, but can save state to disk and pick up where it left off, using flat files for queue input, just appending rsync output. This allows use of EC2 instances for a couple hours every day, churn through the priority chunks (which are chunks that are most active in the world, therefore more likely to be wanted rendered often), and get through as many of the standard queue and world as possible.

* using some basic status metrics, you could see render rates, and how fast it is getting through the priority, updated, and world queues. From this, you can tweak the thresholds.

One other situation that I'm keeping in mind: if you have many active players creating large structures in seperate parts of the map, you may end up with a queue which grows faster than you can render it, meaning the rest of the map never gets rendered. I think a good mitigation would be to purge and disable the standard and priority queues for a set period each day (ie, the server low-time from say 8am-10am for us, or for the last hour of the instance), which lets the process take a big chunk of the world and render it. Keep the list of chunks sorted by last render time, and over time the entire world will be rendered.

Final result is the ability to start rendering a map on an existing large world without the 24hour+ overhead of an initial render (times three if you want lighting branches like us :) ). Most active building spots get rendered as often as you save (or as often as you fire up the instance), and the rest of the map is slowly filled in as it can get to it. Might be days, weeks, or months, but the 'interesting' bits of your map are immediately accessible.

* Awesome thought, replace un-rendered tiles with placeholder yellow/black 40% opacity 'under construction' images, very little overhead (could render in a couple minutes, perhaps?).

I'd love feedback on this idea, before I get started. It's not suited to most deployments, so I don't really see it being merged into brownan's package. But I think if the core image processing code can be kept in line with any upstream changes, we can make a workable package suited for large maps.

-- end text wall --
  
  
  

Running
-------
!TODO!