# Installing the BeamNG.tech Simulator
* Get the licence for the BeamNG.tech simulator. It can be requested at <https://register.beamng.tech/>.
* Download the BeamNG.tech simulator. The download link is provided when you obtain the licence.
* Extract the simulator to a suitable location, for example to `C:\Users\<username>\BeamNG`.
* Place the licence file `tech.key` under `C:\Users\<username>\Documents\BeamnNG.research`.
* Edit the SUT parameter `beamng_home` to reflect the path the simulator was extracted, e.g., set it to `C:/Users/<username>/BeamNG/BeamNG.tech.v0.24.0.1`.
* Install the required packages (see requirements.txt). Currently it is known that everything works correctly with BeamNG.tech version 0.24.0.1 and beamngpy version 1.21. For example, beamngpy 1.23 does not work with the aforementioned simulator version.
* Using the DAVE-2 model requires Tensorflow version 2.4.1.

