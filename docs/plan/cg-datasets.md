
	•	Introduction

The "AI for Good" initiative by ITU highlights how data analysis drives impactful solutions, like using artificial intelligence to achieve Sustainable Development Goals (SDGs). ITU AI ML Challenges have compiled public datasets over a period of 2020-2024. Similarly, the United Nations Guide on Privacy-Enhancing Technologies (PETs) emphasizes the role of data analysis in ensuring privacy while unlocking insights for public good, such as improving healthcare or disaster response.  

As discussed in the modified scope of the CG in SG13-TD265-R1/PLEN, 
- an enhanced study of datasets helps in identification of the specific problems to be solved leveraging the described datasets, models and tools  
- the datasets considered here helps to study of the datasets applicable for AI/ML not only in networks but also applications and services enabled by networks, 
- many of these datasets can help in Strengthening the collaboration within ITU-T and outside ITU-T
(including inputs related to use cases, datasets, models and tools for topics related to networks, and applications and services, with other SGs, SDOs and industry bodies)
	•	Specific efforts are made in Linkage with the AI/ML Challenges initiative and other pre-standards AI/ML activities

This report provides a comprehensive overview of publicly available datasets, emphasizing their significance in fostering innovation, and research. It explores datasets spanning diverse domains, including agriculture, healthcare, environment, education, and urban planning, showcasing their potential to address global challenges.  

Based on the open data available, numerous use cases can be developed across various domains. The datasets are derived from diverse applications highlighted in the "ITU AI/ML Challenges" and the UN PET Guide report.  

All the models and tools mentioned are accompanied by reference papers that provide comprehensive details about their design, functionality, and implementation.    

All the datasets mentioned are supported by reference papers that provide detailed insights into their methodology, and applications. These papers serve as essential documentation, offering a deeper understanding and relevance to various use cases. By referencing these papers, users can build models, design tools, and develop solutions grounded in robust, well-documented data sources.

Based on the analysis of use cases, future work, and overarching abstractions, we have identified several potential standard gaps that need to be addressed. These gaps highlight areas where existing frameworks, methodologies, or tools fall short in effectively supporting emerging applications.  

NOTE- this document is a revision of 
	•	CGD-I-03 presented on 19 December 2024 and 
	•	the CG Datasets document presented on 27 Feb 2023
	•	Datasets 

Editor Note – 
Currently a summary table is provided in Appendix A.
Description based on the table in Appendix A will be provided by the next meeting.

Appendix A includes total 121 datasets with 
	•	68 datasets are ITU AI/ML Challenge (2024-2020) related, out of which:
	•	45 datasets accessible and confirmed as available.
	•	23 datasets are not accessible.
	•	The rest of the datasets are from Geo AI Challenges (2024-2023), AIforGood Innovate for Impact use cases, ITU WTSA Hackathon use cases, ITU Kaleidoscope 2024 Presentations, UN PET guide and other sources.
	•	References

	•	Think-a-Thon 2024 Challenge: UN Metaverse Think-a-Thon 2024 - Virtual Worlds Revolutionizing Smart Sustainable Cities & Communities.
The Metaverse Think-a-Thon 2024 challenges you to push the boundaries of creativity and innovation, designing virtual simulations that transcend traditional brainstorming methods - https://www.itu.int/metaverse/un-virtual-worlds-day/thinkathon/ 

	•	Webinar on UN Metaverse Think-a-Thon: https://itu.zoom.us/rec/play/LbyiVW1LaUAGr5-mx8UUQLQW6XNCL63K4ZIA3CQdQbG-9YznO2ihtU9_GAlAhWuccOJZdDFT8KBLqZfe.AK-F2scMHt7PFzUw?canPlayFromShare=true&from=share_recording_detail&continueMode=true&componentName=rec-play&originRequestUrl=https%3A%2F%2Fitu.zoom.us%2Frec%2Fshare%2F_mL5YaZ7U30cbzvBgvAexjPTuLDBPeyPqhf_PnV-b1IFu1PjQRoTRv9C_uj1-gJ1.TuzDWIWEZcZtwhC8

	•	Linux Foundation: https://lf-anuket.atlassian.net/wiki/spaces/HOME/pages/21890051/Collaboration+-+ITU 

	•	Innovate for Impact Report for 2024 - https://www.itu.int/net/epub/TSB/2024-AI-for-Good-Innovate-for-Impact-final-report/index.html#p=1 

	•	UN PET guide : https://unstats.un.org/bigdata/task-teams/privacy/guide/2023_UN%20PET%20Guide.pdf 
	•	Conclusions and future steps

By cataloguing and analysing datasets from diverse domains such as 5G, application areas such as agriculture, healthcare, environment, and urban planning, including The ITU "AI for Good" initiative and the UN PET Guide we study how data analysis can enable solutions. Reference papers accompanying the datasets, models, and tools ensure credibility, transparency, and effective application across various use cases. Moreover, identifying potential standard gaps paves the way for enhancing interoperability, scalability, and ethical usage in future implementations.

The next steps include
	•	Discuss with specific partners and authors of the datasets and expand specific standards gaps identified here.
	•	Discuss reference solutions (e.g. customised datasets, models and tools and ITU AI/ML Challenges) with partners and authors of datasets in Appendix A. This may be used as a step towards creating detailed standards analysis. 
 

Appendix A: Summary table



NOTE: Colour Legend (as of the document date)
	•	Green – Confirmed accessible dataset.
	•	Red – Dataset not accessible.

NOTE- Following datasets are taken from the GitHub link here: 
	•	https://github.com/ITU-AI-ML-in-5G-Challenge/AI-ML-in-5G-Challenge.github.io?tab=readme-ov-file 

2024 Challenge datasets are taken from:
https://challenge.aiforgood.itu.int/match  and
https://zindi.africa/competitions?query=itu  

Dataset ID
Dataset Title
Description
Example usecases
Dataset links, Example model and tools
Sample notebooks/ GitHub links
Reference Papers
Potential Standard gaps

ITU AI/ML 2024 Challenges
1
Next-Gen tinyML Smart Weather Station Challenge 2024
Several stations have been installed to gather data, which collectively constitutes the final dataset. Each sample collected respects a specific binary format occupying a defined number of bytes. The data within each sample or packet is possess exactly 49196 bytes.

Here you can find the Aurora dataset. Each .zip file contains one week of collected data for one specific station.

Next-Gen tinyML Smart Weather Station Challenge 2024
https://aurora.portal.csem.ch/dataset.html

Data is accessible using the above link.

Challenge link:  https://challenge.aiforgood.itu.int/match/matchitem/91 

Contacts: 
jona.beysens[at]csem.ch 
robin.berguerand[at]csem.ch 
Sample GitHub solution: https://github.com/ITU-AI-ML-in-5G-Challenge/TinyML-Smart-Weather-Station-CSEM 
https://github.com/ITU-AI-ML-in-5G-Challenge/ITU-2024-GenStorm-Submission-Next-Gen-TinyML-Smart-Weather-Station 
tinyML Smart Weather Station Challenge 2024: The Next Generation Returns: https://youtu.be/NO8y3gwU5lM 
https://www.csem.ch/en/ 

https://aurora.portal.csem.ch/ 

2
Optimal Multi-user scheduling in massive MIMO mobile channels
We provide two realistic channel model datasets, one of which is generated from real-world channel measurement experiments on the RENEW platform on Rice University campus.
The dataset is from channel measurements with a 64-antenna massive MIMO base station at Rice University campus where users are placed in multiple locations including 4 line-of-sight and non line-of-sight clusters and in 25 locations within a cluster. The derived dataset emulates a low-mobility network where users move within a cluster. This dataset includes channels of 64 users. The channel for each user is measured at 52 frequency subcarriers (in OFDM symbols). The provided channel dataset includes channel instances at 500 frames.
Optimal Multi-user scheduling in massive MIMO mobile channels
Dataset 1 (low mobility): https://renew-wireless.org/dataset-iuc.html 

I am unable to download the data 
(server or license issue) 

Dataset 2 (high mobility):
https://drive.google.com/file/d/1P8QJd2OKQ8bS4eDQmb4JIEnVQuWQWiq0/view 

The above link is not working
Contact:
xdurice@gmail.com 

already requested the authors for data
https://github.com/fraunhoferhhi/QuaDRiGa 
Challenge link: https://challenge.aiforgood.itu.int/match/matchitem/93 
Contacts:
Qing An qa4[at]rice.edu Rahman Doost-Mohammady doost[at]rice.edu 
Santiago Segarra segarra[at]rice.edu 
Ashutosh Sabharwal ashu[at]rice.edu
https://dl.acm.org/doi/10.1145/2500423.2505302 




3
Radio Resource Management (RRM) for 6G in-X Subnetworks
Simulation Parameters and Dataset Generation
For dataset generation, 20 subnetworks are deployed in a factory with a 20×20(m^2 ) are, characterized by dense clutter. Radio resources are sparse, and thus, the number of frequency channels is set to ( K = 4 ), compelling subnetworks to share limited resources. Radio propagation parameters (carrier frequency (f_c=6) GHz, channel bandwidth ( BW = 10 ) MHz, transmit powers (p=0) dBm, noise figure ( NF = 5 ) dB, and decorrelation distance (d_c=5) meters) are fixed for all simulation results
Radio Resource Management (RRM) for 6G in-X Subnetworks
https://zenodo.org/records/10908382 

Data is accessible using the above link.

Challenge link:  https://challenge.aiforgood.itu.int/match/matchitem/94
Contact:
saehak[at]es.aau.dk 
Radio Resource Management for 6G in-X Subnetworks: https://youtu.be/IgwkVSsP6Pw 

Berardinelli, Gilberto, et al. “Extreme communication in 6G: Vision and challenges for ‘in-X’ subnetworks.” IEEE Open Journal of the Communications Society 2 (2021): 2516-2535.

4
Estimation of Site-specific radio propagation loss
The data is from "PLATEAU Open Data 3D Urban Model Chuo-ku[1] and Chiyoda-ku[2]” (Ministry of Land, Infrastructure, Transport and Tourism, Japan). The offered data is created by a file format conversion.

Estimation of Site-specific radio propagation loss


https://www.geospatial.jp/ckan/dataset/plateau-13102-chuo-ku-2023 

https://www.geospatial.jp/ckan/dataset/plateau-13101-chiyoda-ku-2023 

Data is accessible using the above link.

Contact: KDDI Research, Inc. Kazuki TAKEZAWA, Satoshi ITO, Tatsuya NAGAO and Hiroyuki SHINBO
ITU AI/ML in 5G Challenge | Challenge Program Estimation of Site-specific radio propagation loss: https://youtu.be/C4np69oTXQ0
AI/ML Challenge Finale: Beam-Level Traffic Forecasting and Site-specific radio propagation loss: https://youtu.be/015SVnOV6dE
Challenge link: https://challenge.aiforgood.itu.int/match/matchitem/96 
https://ieeexplore.ieee.org/document/9135876 

https://ieeexplore.ieee.org/document/9977760 

https://ieeexplore.ieee.org/document/9411102 

5
Radio Resource Management (RRM) for 6G in-X Subnetworks [xtended]
In the simulated factory environment, a multitude of strategically deployed short-range cells forms the backbone of robotic systems, production modules, conveyors, and other industrial machinery. These cells, designated as In-factory subnetworks (InF-S), are comprised of an access point (AP) serving one or more devices within the subnetwork.
Radio Resource Management (RRM) for 6G in-X Subnetworks [xtended]
https://zenodo.org/records/10908382  

Data is accessible using the above link.

Challenge link: https://challenge.aiforgood.itu.int/match/matchitem/97
Contact: saehak[at]es.aau.dk 

Radio Resource Management for 6G in-X Subnetworks: https://youtu.be/IgwkVSsP6Pw 

Berardinelli, Gilberto, et al. “Extreme communication in 6G: Vision and challenges for ‘in-X’ subnetworks.” IEEE Open Journal of the Communications Society 2 (2021): 2516-2535.

6
Specializing Large Language Models for Telecom Networks
TeleQnA is a comprehensive dataset tailored to assess the knowledge of LLMs in the field of telecommunications.
It encompasses 1827 multiple-choice questions distributed across two distinct categories
The 1827 MCQs are also divided in 1461 and 366 questions that compose the train and test1 sets.
Specializing Large Language Models for Telecom Networks
https://zindi.africa/competitions/specializing-large-language-models-for-telecom-networks/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.


Sample GitHub Solution: https://github.com/Nouf-Alabbasi/oKUmura_AI_Telecom_challenge 
https://github.com/KameniAlexNea/specializing-llm-telecom 
Specializing Large Language Models for Telecom Networks: https://youtu.be/Xss43TzJsuI 
NA

7
Spatio-Temporal Beam-Level Traffic Forecasting
Four provided CSV datasets containing network performance metrics for 2,880 beams across 30 base stations. Each base station consists of 3 cells with 32 beams, with data recorded hourly. These datasets encompass a five-week period with data recorded at hourly intervals (as illustrated in Figure 2). These datasets are traffic_DLThpVol.csv, traffic_DLThpTime.csv, traffic_MR_number.csv, and traffic_DLPRB.csv. We remind the participants that the objective is to forecast future values of traffic volume (DLThpVol).
Each dataset corresponds to a specific network performance metric
Spatio-Temporal Beam-Level Traffic Forecasting


https://zindi.africa/competitions/spatio-temporal-beam-level-traffic-forecasting-challenge/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Sample GitHub Solution: https://github.com/SalifouAbdourahamane/Spatio-Temporal-Beam-Traffic-Forecasting 
https://github.com/Ansem-chaieb/Spatio-Temporal-Beam-Level-Traffic-Forecasting
AI/ML Challenge Finale: Beam-Level Traffic Forecasting and Site-specific radio propagation loss: https://youtu.be/015SVnOV6dE
NA

8
Smart Energy Supply Scheduling for Green Telecom
The data includes the power supply of sites collected in different days. In more details, the data is divided into 3 datasets:
Site basic information and grid outage: This dataset includes configuration parameters such as diesel output power (in kW) and battery capacity. It also covers grid-related parameters, including output power (in kW) and planned outages.
Solar power statistics: Contains hourly data that details weather conditions (e.g., Direct Normal Irradiance (DNI), Diffuse Horizontal Irradiance (DHI), and Global Horizontal Irradiance (GHI)) along with the energy output measured in kilowatt-hours (kWh).
Energy consumption statistics: Provides hour-by-hour energy consumption details, such as the total energy used by the base stations.
Smart Energy Supply Scheduling for Green Telecom
https://zindi.africa/competitions/smart-energy-supply-scheduling-for-green-telecom/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.


Sample GitHub Solution:
https://github.com/ElfIncredible/Smart-Energy-Supply-Scheduling-for-Green-Telecom/blob/main/README.md 
Smart Energy Supply Scheduling for Green Telecom launch webinar: https://neuralnetwork.aiforgood.itu.int/event/ai-for-good/auditorium-archive/618bd56f1ca6ce6ae07960c9/timeslot/66a9eaf445fc7f81fd7a0df2 
https://www.bing.com/ck/a?!&&p=4c5755a7567d4b2ba5dc9c8882fcddef37b8182d5fceefedb49652bb83b82002JmltdHM9MTczODQ1NDQwMA&ptn=3&ver=2&hsh=4&fclid=2b4907d4-2f91-68b5-3cc5-16942e0a6908&psq=smart+energy+supply+scheduling+for+green+telecom+challenge+by+ITU&u=a1aHR0cHM6Ly93d3cuaXR1LmludC9yZWMvZG9sb2dpbl9wdWIuYXNwP2xhbmc9ZSZpZD1ULVJFQy1MLjEzODAtMjAxOTExLUkhIVBERi1FJnR5cGU9aXRlbXM&ntb=1 


ITU AI/ML 2023 Challenges
9
cell-level traffic statistics of 4G/5G
The data includes cell-level traffic statistics of 4G/5G sites collected on different days.
The data is divided into 3 datasets:
	•	Base Station basic information (BSinfo.csv):
	•	Cell-level data (CLdata.csv): include hour-level counters, including service compliance counters (e.g., load) and energy-saving methods counters (e.g., duration of energy saving mode activation). 
Energy consumption data (ECdata.csv)
AI/ML for 5G-Energy Consumption Modelling
https://zindi.africa/competitions/aiml-for-5g-energy-consumption-modelling/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/83

Contact: 
Nicola Piovesan nicola.piovesan[at]huawei.com
https://zindi.africa/competitions/aiml-for-5g-energy-consumption-modelling/discussions?theme=Notebooks 

AI/ML for 5G-Energy Consumption Modelling: https://youtu.be/zSetefnu3y8 
5G-Energy Consumption Modelling: AI/ML solutions for Climate Change: https://youtu.be/G5CTO2ANOqk 
[1] N. Piovesan, D. López-Pérez, A. De Domenico, X. Geng, H. Bao, M. Debbah, “Machine Learning and Analytical Power Consumption Models for 5G Base Stations”, IEEE Communications Magazine, 60(10), 56-62, 2022

10
Millimeter-Wave Channel Sounding and Modeling
The data set consists of mmWave MIMO channel impulse responses and the corresponding depth map representation of the room. The dataset is obtained using the NIST high-precision 3D double-directional 60 GHz channel sounder, which beyond conventional RF information, collects depth maps by using a lidar. During the measurement campaign, one node is fixed, while the second node is moving and collecting information in more than 6000 locations of the room.
Digital Twin enabled 6G Depth Map Estimation in 6G mmWave systems – The challenge tackles one of the key problems to realizing the vision of digital-twin-enabled 6G systems.
Dataset: https://github.com/usnistgov/ML5G-PS-005/tree/main/dataset 

Data is accessible using the above link.

Challenge link:  https://challenge.aiforgood.itu.int/match/matchitem/63 

Contact: 
steve.blandino[at]nist.gov 
https://github.com/usnistgov/ML5G-PS-005 
presentation slides: https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2Fusnistgov%2FML5G-PS-005%2Frefs%2Fheads%2Fmain%2Fdocs%2FDepth%2520Map%2520Estimation%2520in%25206G%2520mmWave%2520systems.pptx&wdOrigin=BROWSELINK 
Digital-twin-enabled 6G: Depth Map Estimation in 6G mmWave systems: https://youtu.be/xaBS6Q6KgO0 
https://www.nist.gov/communications-technology-laboratory/wireless-networks-division/millimeter-wave-channel-sounding-and 

11
RAN KPI data
A dataset with RAN KPI data, collected from over 100 5G and 4G NEs, will be provided to train machine-learning models. For each NE in the network, it provides 7 key KPIs, the duration of a fault, and the “distance” of the NE to the fault in an hourly basis. Specifically, each row includes:
	•	NE ID, which is a unique identifier for each NE;
	•	Hourly timestamp of the data.
6 RAN KPIs that is related to data rate, including Access Success Rate, Resource
Fault Impact Analysis: Towards Service-Oriented Network Operation & Maintenance
https://zindi.africa/competitions/fault-impact-analysis-towards-service-oriented-network-operation-maintenance/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/78
https://zindi.africa/competitions/fault-impact-analysis-towards-service-oriented-network-operation-maintenance 



Contact:   
Antonio De Domenico (antonio.de.domenico[at]huawei.com)
NA

12
real network testbed
Two datasets generated with a real network testbed. Each dataset contains samples generated in several topologies and includes hundreds of network configurations (routing) and traffic flows. In the first dataset traffic is generated using Constant-Bit Rate (CBR) while in the second traffic is generated using Multi-Burst Rate (MBR). In both cases packet size is randomly selected per flow and constant for all packets within the flow. The range of the packet size is between 100 and 1450 bytes.
Network Digital Twin based on neural networks

Graph Neural Networking
https://bnn.upc.edu/challenge/gnnet2023/dataset/ 

Data is accessible using the above link
https://github.com/BNN-UPC/GNNetworkingChallenge/tree/2023_RealNetworkDT 
https://bnn.upc.edu/download/gnnet_challenge_2023_itu-webinar/ 
 https://doi.org/10.48550/arXiv.2212.12070 

13
Intrusion and Vulnerability Detection in Software-Defined Networks (SDN)
Dataset that combines a small portion of real users obtained from our SD-WAN environment with certain known datasets. The dataset encompasses four primary types of samples: Normal flow data, DDoS flow data, Malware flow data, and web-based flow data. Participants will utilize machine learning techniques to develop an intrusion detection model based on this dataset.
Intrusion and Vulnerability Detection in Software-Defined Networks (SDN)
Data is not available.
We requested the data from Ulak communications. 

Challenge link:  https://challenge.aiforgood.itu.int/match/matchitem/81 

Contact: Evren Tuna - evren.tuna[at]ulakhaberlesme.com.tr Abdullah Mekki - abdullah.mekki[at]ulakhaberlesme.com.tr
Machine Learning for SDN security: improving intrusion and vulnerability detection:  https://youtu.be/zgne_H0Ki7M 
Canadian Institute for Cybersecurity

14
Berlin V2X dataset
The Berlin V2X dataset offers high-resolution GPS-located wireless measurements across diverse urban environments in the city of Berlin for both cellular and side link radio access technologies, acquired with up to 4 cars over 3 days. The data enables thus a variety of different ML studies towards vehicle-to-anything (V2X) communication to lay the foundations of vehicular communications of the future.
Multi-environment automotive QoS prediction
https://ieee-dataport.org/open-access/berlin-v2x 

Data is accessible using the above link and you have to create a free ieee account to download the data.
https://github.com/fraunhoferhhi/BerlinV2X 
MobileInsight: http://www.mobileinsight.net/ 
Multi-environment automotive QoS prediction using AI/ML:  https://youtu.be/XLmIa59BS7w 
Berlin V2X: A Machine Learning Dataset from Multiple Vehicles and Radio Access Technologies
https://arxiv.org/abs/2212.10343 

15
Network Traffic Scenario Prediction
The train set contains 78 network scenarios, and the test contains 19 scenarios. Each piece of training or test data is a log data generated during one completed flow sending process, and all data includes several similar processes.
Network Traffic Scenario Prediction
https://zindi.africa/competitions/network-traffic-scenario-prediction-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
You can view more about the challenge here: https://zindi.africa/competitions/network-traffic-scenario-prediction-challenge 

Sample GitHub Solutions:  https://github.com/SaifNOUMA/Network-Traffic-Prediction 

https://github.com/SnehilSharma31/Enhancing-Real-Time-Network-Traffic-Scenario-Prediction-with-GRU-based-RNN-Architecture 
NA

16
QoS Prediction data
The data includes information on:
	•	Physical layer parameters (such as signal strength and signal quality).
	•	Cellular radio resource management like cell identity, modulation and coding scheme, assigned resource blocks, and carrier aggregation (i.e., primary/secondary cell data).
	•	Wireless Quality-of-Service (QoS) in the form of downlink throughput.
	•	GPS-positioning information.
Side information (traffic and weather).
QoS Prediction
https://zindi.africa/competitions/qos-prediction-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Sample GitHub links here: https://github.com/Nizar-Charrada/QoS_Prediction_Challenge_Second_Place_Solution 
https://github.com/fraunhoferhhi/BerlinV2X 
https://arxiv.org/abs/2212.10343 

http://www.mobileinsight.net/ 

17
Title Extraction
Frame images extracted from webinar videos containing presentation slides with one or more titles.
training slide images may contain up to 4 titles at once, which is reflected in Train.csv

Title Extraction in Lecture Slides
https://zindi.africa/competitions/title-extraction-in-lecture-slides-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/74 
https://github.com/espnet/espnet 



Contact: 
Kirill.Ekshembeev@itu.int; Bastiaan.Quast@itu.int
https://medium.com/@bethworthy/what-is-word-error-rate-measuring-the-wer-of-machine-generated-transcripts-and-its-limitations-1457be914f3b 

18
KDDI datasets - Network failure classification model using network digital twin.
The data were prepared on two mobile core domains in the lab. Both mobile core domains were deployed using VNFs on the OpenStack infrastructure. 5 types of failures were injected on 3 types of VNFs on each domain while the performance data of VNFs were collected including memory, CPU, and traffic information, which generated data with total 16 labels including normal.
Network failure classification model using network digital twin. 

Root Cause Analysis (RCA) model.
Data source not provided. 
 contact given: 
aiml-challenge[at]list.kddi-research.jp 

We requested the data from KDDI Team   

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/84 
wide spread of Network Function Virtualization (NFV) technology, a plenty of Virtualized Network Functions (VNFs) and Cloud-native Network Functions (CNFs) has been deployed in telco 5G mobile networks. 
draft-irtf-nmrg-network-digital-twin-arch: “Digital Twin Network: Concepts and Reference Architecture”
https://arxiv.org/html/2406.06595v1#S3 

19
Deep Sense 6G
A Large-Scale Real-World Multi-Modal Sensing and Communication Dataset for
6G Deep Learning Research
Datasets were built based on the DeepSense data from the V2V scenarios 36 – 39
Scenarios 36 – 39 are collected in an outdoor wireless environment and are explicitly designed to study high-frequency V2V communication in the real world. The DeepSense testbed 6 is utilized in the data collection. It consists of two units: (i) Unit 1, mobile receiver (vehicle) equipped with four 60-GHz mmWave Phased arrays facing four different directions, i.e., front, back, left, right. Each phased array adopts a uniform linear array (ULA) with 16 elements and utilizes an over-sampled pre-defined codebook of 64 beam directions to receive the transmitted signal.
Multi Modal V2V Beam Prediction
https://www.deepsense6g.net/scenarios36-39/ 

Data is accessible using the above link and you have to sign in to get the data.

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/90
Contact: Ahmed Alkhateeb – alkhateeb[at]asu.edu 
sample notebooks/GitHub: https://github.com/DeepSense6G/Multi-Modal-V2V-Beam-Prediction-Challenge-2023-Baseline 






https://deepsense6g.net/

https://www.deepsense6g.net/beam_prediction_challenge_2023/ 


20
3D Location Estimation Using RSSI of Wireless LAN
The developed localization algorithm/technique needs to estimate the position of the receiver given (i) RSS information from transmitters whose positions are known in advance, (ii) information about the surrounding buildings such as RSSI measured with time stamp and SSID, time-series GPS data (Latitude and Longitude) of the transmitter, channel setting, and map information of the measurement area to analyze LoS/NLoS condition in each wireless communication link.
3D Location Estimation Using RSSI of Wireless LAN
Data sources are not provided.

Contact given: ai_ml_challenge@awcc.uec.ac.jp 
We requested the data
Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/89  
N. Bulusu, J. Heidemann, and D. Estrin, “GPS-less low-cost outdoor localization for very small devices,” IEEE Personal Commun., vol. 7, no. 5, pp. 28-34, Oct. 2000, doi: 10.1109/98.878533. 

21
Next-Gen tinyML Smart Weather Station
This dataset contains microphone recordings and environmental sensor data (temperature, humidity and pressure). In addition, it will come with ground truth information from a mechanical weather station, which gives information about the wind and rain intensity.
Next-Gen tinyML Smart Weather Station
Dataset source:
https://portal.csem.ch:9120/ 

The above link is not working.

Contact given: 
jona.beysens[at]csem.ch
robin.berguerand[at]csem.ch

Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/85 
Sample GitHub Solution: https://github.com/ITU-AI-ML-in-5G-Challenge/TinyML-Smart-Weather-Station-CSEM 

[1] Adafruit. 2009. Small 6V 1W Solar Panel. https://www.adafruit.com/product/3809.(2009). [Online; accessed 03-October-2022].
[2] Adafruit. 2011. Adafruit Universal USB / DC / Solar Lithium Ion/Polymer charger- bq24074. https://www.adafruit.com/product/4755. (2011). [Online; accessed03-October-2022].

22
Scalable and High-Performance TinyML Solutions for Plant Disease Detection
Plant-Disease Open Datasets:
he plants disease dataset comprises images of multiple plant species exhibiting signs of diseases, pests, or nutrient deficiencies. Participants are required to develop tinyML models that can not only accurately classify these plant diseases but also ensure scalability to accommodate a wide range of species and conditions. The solutions should provide actionable insights for farmers and agricultural experts, aiding in the prevention and management of plant diseases.
Scalable and High-Performance TinyML Solutions for Plant Disease Detection
1. The YEESI Lab Dataset: https://zenodo.org/record/7729285#.ZFuGnXZBxaT 

2. Plant Village-Dataset: https://github.com/spMohanty/PlantVillage-Dataset and
https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset 

3. DiaMOS Plant Dataset: A Dataset for Diagnosis and Monitoring Plant Disease: https://zenodo.org/record/5557313#.ZFuG0nZBxaQ 

Data is accessible using the above links.
https://github.com/mallociFrancesca/leaf-disease-toolbox 
Hardware support: https://docs.google.com/forms/d/e/1FAIpQLScjnvtUOg5zUYLaaRmhqyFJygTCWOmSpyc3W0-_YGOr-UNfyA/viewform 

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/87 
Contact: 
AI5GChallenge[at]itu.int 
https://doi.org/10.3390/agronomy11112107
G. Fenu and F. M. Malloci,"Using Multi-Output Learning to Diagnose Plant Disease and Stress Severity", Complexity, Article ID 6663442,doi.org/10.1155/2021/6663442,2021. 

23
Scalable and High-Performance TinyML Solutions for Wildlife Monitoring
Wildlife Monitoring
The camera trap dataset contains images captured in natural habitats, featuring diverse wildlife species and their activities.
This data set contains 4747 sequences of camera trap images, totalling 10072 images, from the Snapshot Kruger project, part of the Snapshot Safari network. Using the same camera trapping protocols at every site, Snapshot Safari members are collecting standardized data from many protected areas in Africa, which allows for cross-site comparisons to assess the efficacy of conservation and restoration programs. Kruger National Park, South Africa has been a refuge for wildlife since its establishment in 1898, and it houses one of the most diverse wildlife assemblages remaining in Africa. The Snapshot Safari grid was established in 2018 as part of a research project assessing the impacts of large mammals on plant life as boundary fences were removed and wildlife reoccupied areas of previous extirpation.
Scalable and High-Performance TinyML Solutions for Wildlife Monitoring
1. https://cthulhu.dyn.wildme.io/public/datasets/wild.tar.gz 

2. Snapshot Kruger: https://lila.science/datasets/snapshot-kruger

3.  https://github.com/dhruvmsheth/EleTect-Image-Dataset 

Data is accessible using the above links.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/88 

Contact:
AI5GChallenge[at]itu.int 
Sample GitHub solution:
https://github.com/AI4D-Research-Lab/AI4D-Lab-tinyML-Challenge-03-Scalable-and-High-Performance-TinyML-Solutions-for-Wildlife-Monitoring 
https://www.seeedstudio.com/blog/2023/09/21/revolutionizing-wildlife-monitoring-tinyml-iot-and-lora-technologies-with-xiao-esp32s3-sense-and-wio-e5-module/ 
https://www.nature.com/articles/s41597-023-02118-x 
https://www.nature.com/articles/sdata201526#MOESM66 



ITU AI/ML 2022 Challenges
24
Build your own Closed loop
Collaboratively create a crowdsourced, baseline representation for AN closed loop (controllers), review and analyze them, and publish them in an open repository.
Trigger technical discussions on the standard format for representing closed loops (controllers) with FG AN members and other stakeholders (e.g. IRTF NMRG, TOSCA, et al).
Build your own Closed loop
No data is required. However, use cases for closed loops are required which are openly published by many SDOs including ITU-T FG AN. These would be compiled and discussed in FG AN before launching the Challenge.

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/68 
[FGAN-O-013-R1]

[3GPP TR 28.861]

[NMRG IBN use cases]

[ETSI ZSM 001]
[FGAN-O-013-R1] 

25
Classification of Home Network Users to Improve User Experience
We divide the data into training sets, validation set and test set. We divide the data according to the ratio of 6:2:2. Competitors can also divide the data by themselves.
Each dataset contains two parts: UGE and UBE.
The column fields for each user file are: day, hour, specific time, indicator1, indicator2, indicator3, indicator4, indicator5, indicator6, indicator7, indicator8. The first three fields are time fields, and the last eight fields are key indicator data.

Classification of Home Network Users to Improve User Experience
Data is not provided. 
 Contact given:
Qingxian Xie: xie.qingxian@zte.com.cn

Additional Contact:
Cc: yuan.liya@zte.com.cn 

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/73 
Sample GitHub solution:
https://github.com/ITU-AI-ML-in-5G-Challenge/home-network-users-experience-classification-
https://github.com/ITU-AI-ML-in-5G-Challenge/ML5G-PS-012-Team-Spears-9-Classification-of-Home-Network-Users-to-Improve-User-Experience/blob/main/ITU%20AIML%205g%20-%20Spears9%20-v3.0.pptx 
Guo Y , Schuurmans D . Semi-supervised Multi-label Classification[C]// Joint European Conference on Machine Learning and Knowledge Discovery in Databases. Springer, Berlin, Heidelberg, 2012.

26
Depth Map Estimation in 6G mmWave systems
Data set consisting of mmWave MIMO channel impulse responses and the corresponding depth map representation of the room. The dataset is obtained using the NIST high-precision 3D double-directional 60 GHz channel sounder, which beyond conventional RF information, collects depth maps by using a lidar. During the measurement campaign, one node is fixed, while the second node is moving and collecting information in more than 6000 locations of the room.
Depth Map Estimation in 6G mmWave systems
https://doi.org/10.18434/mds2-2645 

https://datapub.nist.gov/od/id/mds2-2645   -- not working

screen shot taken – attached. 

datasupport@nist.gov 
Steve Blandino: steve.blandino@nist.gov 

Clone the repository and try to run
Sample GitHub Solutions: https://github.com/usnistgov/ML5G-PS-005/tree/main?tab=readme-ov-file
https://github.com/ITU-AI-ML-in-5G-Challenge/ML5G-PS-004-Depth-map-estimation-in-6G-mmWave-systems  
Digital-twin-enabled 6G: Depth Map Estimation in 6G mmWave systems: https://youtu.be/xaBS6Q6KgO0

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/63   
Steve Blandino, Anuraag  Bodi, Raied  Caromi, Jack  Chuang, Camillo Gentile, Nada Golmie, Chiehping  Lai, Jelena  Senic (2022), Context-aware mmWave RF Signals Dataset with Lidar and Camera, National Institute of Standards and Technology, https://doi.org/10.18434/mds2-2645 (Accessed 2025-01-26) https://ieeexplore.ieee.org/document/9981572 

27
Federated Traffic Prediction for 5G and beyond
A dataset with real LTE Physical Downlink Control Channel (PDCCH) measurements, obtained using OWL [3] from three different locations, will be provided to train ML models federatively. The dataset is both anonymous, because it is impossible to obtain users’ unique identifiers, and accurate because individual communication can be separated within the dataset for obtaining high-definition traces.
Federated Traffic Prediction for 5G and beyond
Data is not provided.

Contact given: 
Supercom (supercom@cttc.es) 
Paolo Dini (paolo.dini@cttc.es) 
Marco Miozzo (marco.miozzo@cttc.cat) 
Francesc Wilhelmi (fwilhelmi@cttc.cat) 
https://github.com/cn0xroot/LTE 
https://github.com/srsran/srsRAN_4G 
https://srs.io/ 

Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/60 
Konečný, J., McMahan, H. B., Yu, F. X., Richtárik, P., Suresh, A. T., & Bacon, D. (2016). Federated learning: Strategies for improving communication efficiency. arXiv preprint arXiv:1610.05492.

28
Improving Network Digital Twins through Data-centric AI
To generate training datasets, we provide an accurate packet-level network simulator based on OMNeT++ (Docker image). Network simulators are computationally very expensive to simulate real networks at scale. Their cost is proportional to the number of packet events in the network. To make the problem tractable, we have scaled it down. Participants will be able to quickly generate their training datasets on commodity hardware. We put the constraint that training datasets must have a maximum of 100 samples, and these samples must be from small networks of up to 10 nodes.
Graph Neural Networking Challenge 2022: Improving Network Digital Twins through Data-centric AI
https://github.com/BNN-UPC/GNNetworkingChallenge/tree/2022_DataCentricAI/test_dataset

Data is accessible using the above link.

Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/69

Contact not given.
Technical Report: https://bnn.upc.edu/download/technical_report_routenet_fermi/ 
https://github.com/BNN-UPC/GNNetworkingChallenge/blob/2022_DataCentricAI/quickstart.ipynb 
https://github.com/BNN-UPC/GNNetworkingChallenge/blob/2022_DataCentricAI/input_parameters_glossary.ipynb 
https://github.com/BNN-UPC/GNNetworkingChallenge/blob/2022_DataCentricAI/dataset_visualization.ipynb 
Improving Network Digital Twins through Data-centric AI | AI/ML IN 5G CHALLENGE: https://youtu.be/jhPNNIXKcXo 
https://bnn.upc.edu/challenge/gnnet2022/ 

29
I/Q-based Beam Classification with the Deep Beam Dataset
The data source is represented by the DeepBeam dataset.
It contains 19 HDF5 files that represent a data collection campaign run on the NI mmWave Transceiver System with four SiBeam 60 GHz radio heads and on two Pi-Radio digital 60 GHz radios. The data collection campaign is described in Section 4 of the DeepBeam paper. 
I/Q-based Beam Classification with the DeepBeam Dataset
https://repository.library.northeastern.edu/collections/neu:ww72bh952 

Data is accessible using the above link. You have to click on downloads and specific Dataset as seen below to access.

https://github.com/wineslab/deepbeam 
https://deepbeam.net/ 

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/62 

Contact:
Michele Polese – m.polese@northeastern.edu 
https://www.pi-rad.io/ 
https://arxiv.org/pdf/2012.14350 
https://dl.acm.org/doi/abs/10.1145/3466772.3467035 

30
Location Estimation Using RSSI of Wireless LAN in NLoS Environment
The dataset contains samples of RSS information and location information obtained by GPS, and information about the surrounding buildings such as RSSI measured with time stamp and SSID, time-series GPS data (Latitude and Longitude) of the transmitter, channel setting, and map information of the measurement area to analyze LoS/NLoS condition in each wireless communication.
Location Estimation Using RSSI of Wireless LAN in NLoS Environment
Data source not provided.


Contact given:
ai_ml_challenge@awcc.uec.ac.jp 

cc to:
fukumotonorihiro@g.ecc.u-tokyo.ac.jp 
nakao@nakao-lab.org 

Challenge Link:
https://challenge.aiforgood.itu.int/match/matchitem/65 

Sample GitHub solution:
https://github.com/ITU-AI-ML-in-5G-Challenge/ML5G-PS-006-Location-Estimation-Using-RSSI-of-Wireless-LAN-in-NLoS-Environment-TeleAILab/blob/3c8b38c52eb819a99336528f710abf5228d3b758/ITU2022RSSIv1(1).pptx 

[1] N. Bulusu, J. Heidemann, and D. Estrin, “GPS-less low-cost outdoor localization for very small devices,” IEEE Personal Commun., vol. 7, no. 5, pp. 28-34, Oct. 2000, doi: 10.1109/98.878533.
https://dl.acm.org/doi/10.1145/3651671.3651706 


31
Machine Learning for Throughput Prediction in Coordinated IEEE 802.11be Wi-Fi networks
The dataset contains several entries for different deployments, i.e., varying the devices position and including the RSSI matrices and the list of the subset of random scheduled APs for each of them. This dataset will be used to train ML models, and then to estimate the most suitable subset of devices around each AP, as well as the aggregate throughput achieved using these selections.
The dataset is generated on Matlab. It is intended for training a machine learning model that has to be able to estimate the throughput. The dataset is split into several files (10000), each of them contains the information about one deployment. At every deployment, the number of stations as well as their positions are randomly generated. Once the scenario is generated, APs start transmitting and they are randomly selected for all TXOPs (100 TXOPs per deployment).
Machine Learning for Throughput Prediction in Coordinated IEEE 802.11be Wi-Fi networks
Data source is not provided.

Contacts given:

David Nunez (david.nunez@upf.edu)  Rashid Ali (rashid.ali@upf.edu)  Boris Bellalta (boris.bellalta@upf.edu) 
francesc.wilhelmi@gmail.com 

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/66 
Introducing IEEE 802.11be: The Wi-Fi of the future: https://youtu.be/oIJclFfaCvo 
D. Nunez, F. Wilhelmi, S. Avallone, M. Smith and B. Bellalta, “TXOP sharing with Coordinated Spatial Reuse in Multi-AP Cooperative IEEE 802.11be WLANs,” 2022 IEEE 19th Annual Consumer Communications & Networking Conference (CCNC), 2022, pp. 864-870, doi: 10.1109/CCNC49033.2022.9700500.


32
Multi Modal Beam Prediction Challenge 2022: Towards Generalization
DeepSense 6G Scenarios
Developing efficient solutions for sensing-aided beam prediction and accurately evaluating them requires the availability of a large-scale real-world dataset. With this motivation, we built the DeepSense 6G dataset, the first large-scale real-world multi-modal dataset with co-existing communication and sensing data. Fig. 4 highlights the DeepSense 6G testbed and the overall data collection and post-processing setup.
Multi Modal Beam Prediction Challenge 2022: Towards Generalization
https://challenge.aiforgood.itu.int/match/matchitem/72
Datasets are given in the above link.

Data is accessible using the above link and you have to sign in to download the data.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/72

Contact:  competition@deepsense6g.net 
https://www.deepsense6g.net/multi-modal-beam-prediction-challenge/ 
https://github.com/DeepSense6G/Multi-Modal-Beam-Prediction-Challenge-2022-Baseline 
https://github.com/ITU-AI-ML-in-5G-Challenge/DeepSense6G_TII 
https://arxiv.org/abs/2209.07519 
https://www.researchgate.net/publication/363584829_Multi-Modal_Beam_Prediction_Challenge_2022_Towards_Generalization 

33
Network failure prediction on CNFs 5GC with Linux eBPF
Multi-variant time-series metrics obtained by cAdvisor, eBPF, and 5G log for each 5GC CNF under normal and failure conditions. The provided data were generated in the CNF-based 5GC test environment. The failure injector causes packet loss on the 5GC intentionally, extending the loss rate time by time, while the data collector obtains metrics from the 5GC.
The data consists of training and test data, both of which include labels, time-series metrics as shown in Fig. 5. The details of dataset such as time, label, and metrics.
Network failure prediction on CNFs 5GC with Linux eBPF
Data source is not provided.

Contact given:
nw_ai@list.kddi-research.jp

Challenge Link:
https://challenge.aiforgood.itu.int/match/matchitem/64 
https://ebpf.io/
https://github.com/google/cadvisor 
https://github.com/ITU-AI-ML-in-5G-Challenge/ML5G-PS-005_MLAB-NFP 
https://ieeexplore.ieee.org/document/10200028 
https://www.jstage.jst.go.jp/article/comex/13/5/13_2023XBL0183/_pdf/-char/en 

34
Next-Gen Wi-Fi Throughput Prediction Challenge
The dataset contains several entries for different deployments, i.e. varying the device’s position and including the RSSI matrices and the list of the subset of random scheduled APs for each of them.
The dataset is split into 10 000 files, each containing information about one deployment. At every deployment, the number of stations as well as their positions are randomly generated. Once the scenario is generated, APs start transmitting and they are randomly selected for all TXOPs (100 TXOPs per deployment).
Next-Gen WiFi Throughput Prediction Challenge
https://zindi.africa/competitions/next-gen-wifi-throughput-prediction-challenge/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.


Contact: francesc.wilhelmi@gmail.com 
Request for reference.
Sample GitHub solution: https://github.com/Iheb-ch/Next-Gen-WiFi-Throughput-Prediction-Challenge-by-ITU-AI-ML-in-5G-Challenge/blob/main/StarterNotebook.ipynb 
Next-Gen WiFi Throughput Prediction | Machine Learning 5G challenge: https://youtu.be/jwhDMyMvBZM 
ML for Throughput Prediction in Multi-AP Wi-Fi Networks using Spatial Reuse | AI/ML IN 5G CHALLENGE: https://youtu.be/tfBwh9ckSSE 
https://arxiv.org/pdf/2203.10472 
https://www.itu.int/dms_pub/itu-s/opb/jnl/S-JNL-VOL3.ISSUE2-2022-A11-PDF-E.pdf 

35
Non-linear Power Amplifier Behavioral Modeling to achieve higher energy efficiency in 5G RAN
Datasets: 1 training dataset and 4 testing datasets. Data files in both .mat and .dat format are provided for your option.
Each dataset contains the one input and the corresponding output signal sequence of the PA. All the datasets are collected from the same PA.
Non-linear Power Amplifier Behavioral Modeling to achieve higher energy efficiency in 5G RAN
Data source is not provided.

Contact given:

Contact Yisheng Fang: fang.yisheng@zte.com.cn 

Cc to: yuan.liya@zte.com.cn 

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/70 
Sample GitHub Solution:
https://github.com/ITU-AI-ML-in-5G-Challenge/Team-MLAP-solution-for-ML5G-PS-007-Non-linear-Power-Amplifier-Behavioral-Modeling/blob/main/README.md 
F. M. Ghannouchi and O. Hammi, “Behavioral modeling and predistortion,” in IEEE Microwave Magazine, vol. 10, no. 7, pp. 52-64, Dec. 2009, doi: 10.1109/MMM.2009.934516.

36
"Slidin' videos": Slide Transition Detection and Title Extraction in Lecture Videos
Recordings of 100 “AI for Good” (https://aiforgood.itu.int/) webinars were sourced to assemble a diverse collection of more than 240 video presentations made by members of the scientific community, entrepreneurs, and standardization experts.
Video file covering presentation from when presenter started screenshare right to the moment when it was turned off.
Annotation specifying frame-level temporal boundaries of each slide that was shown during a presentation as well as its (apparent) title.
Video files vary in duration (from several minutes to several hours) and resolution (from 1600x1200 to 3840x2160).
Each video in the dataset was recorded at a rate of 25 FPS (frames per second).
"Slidin' videos": Slide Transition Detection and Title Extraction in Lecture Videos
https://aiforgood.itu.int/ 

The dataset is available for teams registered to participate in this problem statement (under Data Download). 

To get the data, write an email to AI5GChallenge[at]itu.int 

Kirill.Ekshembeev@itu.int  Bastiaan.Quast@itu.int 
The above emails are not valid

Editor Note: Check with Thomas on the dataset.
https://github.com/ITU-AI-ML-in-5G-Challenge/PS-000.0-Slidin-videos-Slide-Transition-Detection-and-Title-Extraction-in-Lecture-Video
“Slidin’ Videos”: Slide transition detection and title extraction in lecture videos | AI FOR GOOD: https://youtu.be/2EuuhvLeYdY 

Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/74 
Guan, M., Li, K., Ma, R., An, P. (2020). Convolutional-Block-Attention Dual Path Networks for Slide Transition Detection in Lecture Videos. In: Zhai, G., Zhou, J., Yang, H., An, P., Yang, X. (eds) Digital TV and Wireless Multimedia Communication. IFTC 2019. Communications in Computer and Information Science, vol 1181. Springer, Singapore.

37
Synthetic Observability Data Generation using GANs
Real-World observability data (Telco-Cloud Infrastructure Metrics) will be provided.
Synthetic Observability Data Generation using GANs
Data source is not provided.

Contacts given:

Lei Huang: huangleiyjy@chinamobile.com  Sridhar K. N. Rao: sridharkn@u.nus.edu 

Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/67 
https://wiki.anuket.io/display/HOME/Delivery+and+Assessment 
Synthetic Observability Data Generation using GANs | AI/ML IN 5G CHALLENGE: https://youtu.be/U05ThCezAHg 
https://medium.com/data-science-at-microsoft/synthetic-data-generation-using-generative-adversarial-networks-gans-part-1-47ecbf46b575 
https://towardsdatascience.com/generative-ai-synthetic-data-generation-with-gans-using-pytorch-2e4dde8a17dd 

38
QoS Prediction Challenge AI/ML in 5G Challenge and
5G Campus Network QoS Dataset for Open-Source gNB Implementations
The dataset used was a combination from two sources, one is the Berlin V2X data from Kaggle this was to bring the VANET dynamic nature into the mix and some subsets of the 5G Campus Network QoS Dataset from Zenodo to help broaden the model capability. If there is more QoE/QoS data from your side could be useful for more requirements alignment.

This 5G campus network dataset contains 6 distinct CSV files.
Real-time Network reliability prediction
https://www.kaggle.com/datasets/gauravduttakiit/qos-prediction-challenge-aiml-in-5g-challenge?select=Test.csv

https://zenodo.org/records/13754300

Data is accessible using the above link.

Scikit-learn, LightGBM, Multi-Layer Perceptron

AI/ML Challenge Finale: QoS prediction, Network Traffic Scenario Prediction & SDN Security:  https://youtu.be/kvnc-hM7FaQ 

Sample GitHub:  https://github.com/takalani95/QoS-Prediction-Challenge-by-ITU-AI-ML-in-5G-Challenge/blob/main/QoS_Prediction.ipynb 
https://zenodo.org/communities/sns-origami/records?q=&l=list&p=1&s=10&sort=newest

 
39
Slip Detection and Force Estimation
The input exists in multiple CSV files each relating to an individual time-series of an event of picking up an object of interest that can be deformable and slipping while being picked up.
Slip Detection and Force Estimation
https://bhartischool.iitd.ac.in/build_a_thon/assets/datasets/Task1_ForceEstimation.zip 

Data is accessible using the above link.
Build-a-thon: AI/ML driven Low Latency Closed Loop Control:  https://youtu.be/3eMQpk-v_Cw 

IIT Delhi-Round Table for AI/ML Challenge 2022:  https://youtu.be/UedZYsrTPQg 
https://bhartischool.iitd.ac.in/build_a_thon/index.html 

40
Object Detection

Parse the pre-evaluation dataset and use your model to generate output predictions. These predictions need to be dumped in CSV format such that each line in the CSV file contains a label of the object corresponding to features in each row in the pre-evaluation dataset.
Object Detection

https://drive.google.com/file/d/1Uzg0v91V3xdBK4qk-NBQxykUVVf-OaRb/view

https://bhartischool.iitd.ac.in/build_a_thon/assets/datasets/Task2_ObjectDetection.zip 

Data is accessible using the above link.
Build-a-thon: AI/ML driven Low Latency Closed Loop Control:  https://youtu.be/3eMQpk-v_Cw 

IIT Delhi-Round Table for AI/ML Challenge 2022:  https://youtu.be/UedZYsrTPQg
https://bhartischool.iitd.ac.in/build_a_thon/index.html


ITU AI/ML 2021 Challenges
41
Combinatorial Optimization Challenge: - Delivery route optimization
Each sample in the dataset is composed of 2 elements
1. A Json object that describes the graph of the transportation network
2. A Json object that describes the starting point, endpoint, weight information of each delivery
Combinatorial Optimization Challenge: - Delivery route optimization
Data is not provided. 

Contact given:
yuan.liya@zte.com.cn 
yang.xikun@zte.com.cn 

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/43 
Combinatorial Optimization Challenge: Delivery Route Planning Optimization | AI/ML IN 5G CHALLENGE: https://youtu.be/H6uvVfP5ZPs 

NA

42
Federated Learning for Spatial Reuse in a multi-BSS (Basic Service Set) scenario
A dataset generated with the Komondor simulator is provided to train ML models.
The dataset contains the information of 10.000 IEEE 802.11ax deployments at which the Basic Service Set (BSS) of interest applies different possible OBSS/PD thresholds in the context of the Spatial Reuse (SR) operation. In total, 21 OBSS/PD values are considered for each deployment, so the dataset includes 210.000 simulations, which are expected to be used for training Machine Learning (ML) algorithms. More specifically, the proposed PS is focused on Federated Learning (FL).
Federated Learning for Spatial Reuse in a multi-BSS (Basic Service Set) scenario
https://zenodo.org/records/5352060#.YS9fVtMzba0 

Data is accessible using the above link.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/37

Contact not given.
Sample GitHub Solution:  https://github.com/ITU-AI-ML-in-5G-Challenge/ITU-ML5G-PS-004-spatial-reuse-team-WirelessAI 

The Potential of ML to Address Spatial Reuse in Future IEEE 802.11 WLANs | AI/ML IN 5G CHALLENGE: https://youtu.be/gSPy_PHbsc8 
https://www.upf.edu/web/wnrg/2021-edition 

43
Forecasting Model for Service Allocation Network Using Traffic Recognition
The training data in pcap format

Forecasting Model for Service Allocation Network Using Traffic Recognition
http://khakimov.tech/ITU_dataset.zip
The data link is not working. 

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/42

Contacts not given
Sample GitHub Solution: https://github.com/ITU-AI-ML-in-5G-Challenge/ITU-ML5G-PS-010-Forecasting-Model-for-Service-Allocation-Network-Using-Traffic-Recognition 
https://github.com/SaifNOUMA/Network-Traffic-Prediction 
https://arxiv.org/abs/2410.15322 

44
Graph Neural Networking Challenge 2021 - Creating a Scalable Network Digital Twin
We provide a dataset generated with the OMNet++ network simulator, which is a discrete event packet-level network simulator. The dataset contains samples simulated in several topologies and includes hundreds of routing configurations and traffic matrices. Each sample is labelled with network performance metrics obtained by the simulator: per-flow performance statistics (mean per-packet delay, jitter and loss), and port statistics (e.g. queue utilization, size).
Graph Neural Networking Challenge 2021 - Creating a Scalable Network Digital Twin
https://bnn.upc.edu/challenge/gnnet2021/dataset/ 

Scroll down to see the data. 
Click on the data and you will be able to download it. 

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/31

Contact:  gnnetchallenge <at> bnn.upc.edu 
Sample GitHub Solution: https://github.com/BNN-UPC/GNNetworkingChallenge 
https://github.com/BNN-UPC/GNNetworkingChallenge/blob/main/README.md 

https://bnn.upc.edu/challenge/gnnet2021/ 
https://aiforgood.itu.int/wp-content/uploads/2020/12/GNNet_challenge_2021-2.pdf 

45
Lightning-Fast Modulation Classification with Hardware-Efficient Neural Networks
This challenge uses the RadioML 2018.01A dataset provided by DeepSig. You will be required to provide your contact information to download the dataset.
Please note that this dataset is released by DeepSig under the Creative Commons Attribution - NonCommercial - ShareAlike 4.0 License and you must abide by the terms of this license to participate in our challenge.
Please note that we use a fixed train/test split on the dataset for a fair comparison, and you must abide by this in order to provide a valid submission. This split is given by the fixed random seed and other parameters in the Jupiter notebook we provide in the sandbox.
Lightning-Fast Modulation Classification with Hardware-Efficient Neural Networks
https://www.deepsig.ai/datasets/ 

Click on Dataset Download and enter the information (Name, email). 
You will get the dataset link to your email.
(After receiving the link download within 1hr or it expires later.)

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/34

Contacts: alessand@xilinx.com 
felixj@xilinx.com
mblott@xilinx.com  
yamanu@xilinx.com 
https://github.com/Xilinx/brevitas-radioml-challenge-21 
Lightning-Fast Modulation Classification Hardware-Efficient Neural Networks | AI/ML IN 5G CHALLENGE: https://youtu.be/Mn4_1YeS-IM 
Sample notebooks: https://github.com/Xilinx/brevitas/tree/master/notebooks 
https://www.deepsig.ai/ 
https://creativecommons.org/licenses/by-nc-sa/4.0/ 
https://arxiv.org/pdf/1712.04578 

46
Location estimation using RSSI of wireless LAN
The training data includes the location of AP, RSSI information within the coverage of the AP and its corresponding location.
Location estimation using RSSI of wireless LAN
Data source is not provided.


Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/58 

Contacts given:
nakao@nakao-lab.org  fukumotonorihiro@g.ecc.u-tokyo.ac.jp 
NA
S. Hara and D. Anzai, “Use of Simplified Maximum Likelihood Function in a WLAN-Based Location Estimation” IEEE Conference on Wireless Communications and Networking, pp.1-6, May 2009

47
Multidevice localization with mmWave signals in a factory environment
The training data set consists of a collection of channels associated to the links between devices and access points in a factory environment and their associated positions in the room. The factory environment has been simulated by ray tracing, with 12 access points (AP) located at the ceiling. The devices are randomly placed at the room and assigned to the AP with highest gain during the sector level sweep. For simplification, we assume perfect synchronization, this means that the first path arrives to the AP at time 0. The beam-training is measured. Then, with probabilities 50%, 25% and 25%, 0, 1 or 2 other devices interfere with the beam-training through random 4-QAM OFDM symbols using 512 frequency carriers.
Multidevice localization with mmWave signals in a factory environment
https://research.ece.ncsu.edu/ai5gchallenge-localization/ 

Scroll down to see the data. 
Click on the data and you will be able to download it.


Challenge Link: 
https://challenge.aiforgood.itu.int/match/matchitem/40

Contact:
ngprelcic@ncsu.edu  Tel: +1 512 574 1604
Multidevice Localization with mmWave Signals in Factory Environments | AI/ML in 5G Challenge:  https://youtu.be/aoREh393aBg 
A. Shahmansoori, G. E. Garcia, G. Destino, G. Seco-Granados and H. Wymeersch et al., “Position and Orientation Estimation through Millimeter Wave MIMO in 5G Systems,” IEEE Trans. Wireless Commun., March 2018.

48
Reinforcement learning: scheduling and resource allocation
The dataset is composed of “traces” from simulations executed with Unreal Engine + AirSim.
Reinforcement learning: scheduling and resource allocation
https://nextcloud.lasseufpa.org/s/WYZAMbSbdocs2DL 

Data is accessible using the above link.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/39 

Contact not given.
Radio-Strike: A Reinforcement Learning Game for MIMO Beam Selection in 3-D Environments: https://youtu.be/6o6PUsbaWnA

https://ai5gchallenge.ufpa.br/  
https://ieeexplore.ieee.org/document/8644288 
https://ita.ucsd.edu/workshop/18/files/paper/paper_3313.pdf 

49
Network anomaly detection based on logs
The data is the log data of network equipment, including time stamp, log information, etc. The log is in text format. The data is divided into training set and test set. The training set contains tag information, that is, with exception and without exception; it is a Boolean tag representing a true or false result. The test set comes from the same network equipment as the training set. The test set does not contain tag information. After modelling, the contestants predict the test set and get its tag. The data will be publicly available.
Network anomaly detection based on logs
The dataset is not provided.


Contacts not given.

Challenge Link:
https://challenge.aiforgood.itu.int/match/matchitem/33 
Anomaly Detection Based on Log Analysis | AI/ML IN 5G CHALLENGE: https://youtu.be/LFczu-anqAY 
https://arxiv.org/pdf/2407.05639 


50
Network failure detection and root cause analysis in 5GC by NFV-based test environment.
The data sets used for this challenge were created in the NFV-based test environment simulated for 5GC according to [1]. In this sense, they are synthetic data, but as similar as the real data, resulting from our NFV-based test environment. The data sets consist of normal/abnormal labels, performance monitoring data sets such as traffic volume, various information of a control plane, HW and middleware performance data. Whilst the data sets were kept being stored for a long period enough to be analysed, intentional network failures were applied to the network, leading to abnormal labels.
Network failure detection and root cause analysis in 5GC by NFV-based test environment.
Data source is not provided.

Contact given:
info_itu5G_jp@lists.cc1g.kddi-research.jp 

Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/57 
https://github.com/ITU-AI-ML-in-5G-Challenge/ITU-ML5G-PS-015-Network-failure-detection-in-5GC-team-YOTA-YOTA 
Data is mentioned in the above link
Network Failure Detection & Location Estimation | AI/ML IN 5G CHALLENGE: https://youtu.be/-0zpFjIPBDU 
https://link.springer.com/chapter/10.1007/978-981-99-3010-4_5 

51
Build-a-thon(PoC) Network resource allocation for emergency management based on closed loop analysis
Future mobile networks including 6G are expected to use AI/ML based closed loops for performing various network operations. Our goal is to orchestrate a set of hierarchical autonomous AI/ML based closed loops in the mobile network. These closed loops should be able to perform operations like disaster detection, ML Pipeline management etc. Participants are expected to use relevant simulators as well as the 5G Berlin testbed for this purpose.
Build-a-thon(PoC) Network resource allocation for emergency management based on closed loop analysis
Data source is not provided.


Challenge Link: https://challenge.aiforgood.itu.int/match/matchitem/45 

Contact not given.

https://github.com/ITU-build-a-thon/challenge-resources 
Sample GitHub Solution: https://github.com/ITU-AI-ML-in-5G-Challenge/PS-014-Build-a-thon-PoC-Network-resource-allocation--Team-Conquerors 
https://github.com/krcmehmet/ITUChallenge_BuildaThon_Activity4/diffs/12?base_sha=928481f4966c5614bec4693701588beeda2d59b2&name=GPR&pull_number=1&qualified_name=refs%2Fheads%2FGPR&sha1=928481f4966c5614bec4693701588beeda2d59b2&sha2=1d69ecd4a0672ba9b1b96d0d98eac1055712c9ba&short_path=b335630&unchanged=expanded&w=false 
https://www.academia.edu/111868022/Network_resource_allocation_for_emergency_management_based_on_closed_loop_analysis#:~:text=This%20study%20describes%20the%20major%20results%20from%20building,organized%20by%20the%20Internal%20Telecommunication%20Union%20Focus%20 
https://www.itu.int/dms_pub/itu-s/opb/jnl/S-JNL-VOL3.ISSUE2-2022-A16-PDF-E.pdf 


52
Radio Link Failure Prediction
Given the region-wise, historical data sets derived from our networks and weather forecasts from the meteorology stations predict the occurrence of radio link failures.
Radio Link Failure Prediction
Training Dataset: https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021/blob/main/RLF_Prediction_ITU_AIML_Challenge_Data/RLF_Prediction_ITU_AIML_Challenge_Data.7z 

https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021/tree/main/RLF_Prediction_ITU_AIML_Challenge_Data 

Data is accessible using the above links.
Exemplary Colab Project by Turkcell: https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021/blob/main/RLF_Prediction_ITU_AIML_Challenge_Data/TurkcellExampleProject.ipynb 

Challenge Link:
https://challenge.aiforgood.itu.int/match/matchitem/35 

Contact not given.
https://ieeexplore.ieee.org/document/9685587 

53
RF-Sensor Based Human Activity Recognition
CI4R- Human-Activity-Recognition-Datasets
Human activity dataset from the laboratory of Computational intelligence for Radar (Ci4R) has been made public here.
RF-Sensor Based Human Activity Recognition
https://github.com/ci4r/CI4R-Activity-Recognition-datasets 

Data is accessible using the above link.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/41 

Contact not given.
Sample GitHub Links: https://github.com/ci4r/4-GHz-Human-Activity-Dataset- 
https://console.cloud.google.com/storage/browser/cross-frequency_dataset?authuser=0 
You can also access the data from here
https://doi.org/10.1117/12.2559155 
https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11408/2559155/Cross-frequency-training-with-adversarial-learning-for-radar-micro-Doppler/10.1117/12.2559155.short?SSO=1 

54
WALDO (Wireless Artificial intelligence Location DetectiOn): sensing using mmWave communications and ML.
The training datasets consist of a collection of received packets at different SNR. The IEEE 802.11ay preamble is filtered through the NIST Q-D channel realizations, which model the millimetre wave wireless signal propagation in a room with multiple people moving.
WALDO (Wireless Artificial intelligence Location DetectiOn): sensing using mmWave communications and ML.
https://github.com/usnistgov/PS-002-WALDO/tree/main/dataset 

Data is accessible using the above link.

Challenge Link:  https://challenge.aiforgood.itu.int/match/matchitem/38 

Contact not given.
https://github.com/usnistgov/PS-002-WALDO?tab=readme-ov-file#installation 
NIST Q-D channel realization software: https://github.com/wigig-tools/qd-realization 
ML for Joint Sensing and Communication in Future mm Wave IEEE 802.11 WLANs | AI/ML IN 5G CHALLENGE: https://youtu.be/2LluQUVKwb0 
https://www.nist.gov/ctl/wireless-networks-division 
Slides: https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2Fusnistgov%2FPS-002-WALDO%2Frefs%2Fheads%2Fmain%2Fdoc%2Fps002Waldo.pptx&wdOrigin=BROWSELINK 

55
Cross Layer user experience optimization – Radio link performance prediction
Training data from Radio Intelligent Controller (RIC) [1] testbed over wireless network with CellDLMACRate, DLOccupyPRBNum, ULSINR, DLMACRate, MCS, PDCPOccupBuffer, PDCPUnusedBuffer, DLPDCPSDUNum, DLOccupyPRBNum. Label data from the UE report which contains the application-level data rate.
Cross Layer user experience optimization – Radio link performance prediction
Dataset is not available.

Challenge link: https://challenge.aiforgood.itu.int/match/matchitem/44 

Contact: Qi Sun sunqiyjy@chinamobile.com  
Radio Link Failure Prediction:  https://www.itu.int/en/ITU-T/AI/challenge/2020/Documents/ITUChallenge_LinkBusters.pdf 
O-RAN.WG3.RICARCH-v01.00: “O-RAN Working Group 3;Near-Real-time RAN Intelligent Controller; Near-RT RIC Architecture”.


ITU AI/ML 2020 Challenges
56
5G+AI
(Smart Transportation)
State Farm Distracted Driver Detection

5G+AI (Smart Transportation)
https://www.kaggle.com/c/state-farm-distracted-driver-detection/data

Data is accessible using the above link.
Click on late submissions and accept the terms to download.

https://www.kaggle.com/models/jatentaki/disk/pyTorch/depth-supervision 

Sudhir Kumar Reddy, Girish Varma & C V Jawahar - Cityscale Road Audit System using Deep Learning - International Conference on Intelligent Robots (IROS’18)

57
Graph Neural Networking (GNN) Challenge 2020
This repository contains datasets with simulation results of delay, jitter and packet loss for three different network topologies: NSFNET (14 nodes), GBN (17 nodes) and GEANT2 (24 nodes).
The dataset is divided in two compressed files (.tar.gz) corresponding to the training and validation datasets. The training dataset contains only samples simulated in the NSFNET and GEANT2 network topologies, while the validation dataset contains samples simulated in GBN. Likewise, the test dataset that we will release during the evaluation phase will contain only samples simulated in other topology, with very similar distributions to the samples used in the validation dataset.
Graph Neural Networking (GNN) Challenge 2020
https://bnn.upc.edu/challenge/gnnet2020/ch20-dataset/ 

Data is accessible using the above link.

https://github.com/BNN-UPC/GNNetworkingChallenge 
https://bnn.upc.edu/challenge/gnnet2020/ch20-dataset/ 
https://arxiv.org/abs/2107.12433 

58
channel estimation: Machine learning applied to the physical layer of millimetre-wave MIMO systems
TD1SNR1_example_for_test_data.m is an example of how to obtain the predictions for test data for the test dataset 1- SNR1.
ReconstructChannel.m is the function with our algorithm to obtain the channels. Whitening.m is a subfunction used to whitten the noise on ReconstructChannel.m.
Train.m is the script used for training to obtain the detection threshold. ReconstructChannel_train.m is the function similar to ReconstructChannel.m used during the training script.
channel estimation: Machine learning applied to the physical layer of millimetre-wave MIMO systems
https://onedrive.live.com/?authkey=%21AAA16XOWBQ5tht8&id=61096A69CCAB988B%2185013&cid=61096A69CCAB988B 

Data is accessible using the above link.

Channel Estimation - Physical Layer of Millimeter Wave MIMO Systems | AI/ML IN 5G CHALLENGE:  https://youtu.be/Ygqa7JEiPwI?list=PLQqkkIwS_4kXzAb8yohjHlMVrIx8GNazO 
https://github.com/ITU-AI-ML-in-5G-Challenge/Channel-Estimation-ML-DOJO-2 
https://hal.science/hal-03455706v1/file/Channel_Estimation_Techniques_for_Millimeter-Wave_Communication_Systems_Achievements_and_Challenges_2020_Hassan.pdf 
https://www.itu.int/en/ITU-T/AI/challenge/2020/Documents/ITU%20AI_ML%20Challenge%20-%20ML5GPHY-channel%20estimation.pdf 

59
DNN Inference Optimization Challenge
design a general model optimization algorithm to achieve model acceleration. The target models are as follows:
	•	BERT
	•	MobileNet-V3
	•	ResNet 50


DNN Inference Optimization Challenge
https://storage.googleapis.com/bert_models/2020_02_20/all_bert_models.zip 

Data is accessible using the above link.


https://github.com/google-research/bert
https://github.com/KaimingHe/deep-residual-networks 
https://lf-aidata.atlassian.net/wiki/spaces/ADLIK/pages/13795364/2020+DNN+Inference+Optimization+Challenge 
https://github.com/topics/mobilenet-v3 
https://arxiv.org/abs/1908.08962 
https://www.itu.int/en/ITU-T/AI/challenge/2020/Pages/default.aspx 

60
Improving the capacity of IEEE 802.11 WLANs through machine learning
Self-contained 4-BSS's dataset of spectrum management in WLANs


Improving the capacity of IEEE 802.11 WLANs through machine learning
https://zenodo.org/records/4265898
https://zenodo.org/records/3952557 
https://zenodo.org/records/3960029 

https://github.com/wn-upf/stadia_cloud_gaming_dataset_2020 

All the Data links are accessible using the above link.
Wi-Fi All-Channel Analyzer - WiNTECH 2020 presentation:  https://youtu.be/QxOGX7h-YRc 
https://github.com/sergiobarra/WACA_WiFiAnalyzer 
https://arxiv.org/pdf/2009.09786 


61
Privacy Preserving AI/ML in 5G networks for healthcare applications
All the datasets are taken from Kaggle and IEEE. 
These datasets are related to Chest X-rays. 
All the datasets are free and accessible.
Privacy Preserving AI/ML in 5G networks for healthcare applications
https://www.kaggle.com/datasets/raddar/chest-xrays-tuberculosis-from-india

https://www.kaggle.com/datasets/raddar/tuberculosis-chest-xrays-shenzhen

https://www.kaggle.com/datasets/raddar/tuberculosis-chest-xrays-montgomery

https://www.kaggle.com/datasets/tanlikesmath/diabetic-retinopathy-resized

All the Data links are accessible using the above link.
https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid

https://ieee-dataport.org/documents/automation-and-analysis-chest-x-ray-and-microscopy-images-tuberculosis-detection-0 
Data is accessible using the above link and you have to create a free ieee account to download the data.
https://github.com/elasticdeeplearning/edl
https://github.com/Microsoft/SEAL
https://gitlab.com/palisade/palisade-release 
https://lf-aidata.atlassian.net/wiki/spaces/EDL/overview


62
Using Weather Info for Radio Link Failure Prediction Challenge
Training data will include pre-processed and anonymised RL KPIs from our networks and time-aligned weather data. RL KPI data includes date/time, coordinates, frequency band, link length, error and failure statistics, availability ratio, stability score, capacity, modulation (128QAM, 256QAM, 512QAM, etc.).
Weather forecast data includes coordinates, temperatures (min, max), humidity (min, max), wind speed and direction while the hourly weather realizations data includes precipitation and overcast ratio in addition to them.
Using Weather Info for Radio Link Failure Prediction Challenge
https://mylifebox.com/sharedFiles?publicToken=5f19ec92-da0e-4ab3-bf80-b40817d276a0&language=en 

Dataset link is not working. 

https://aiforgood.itu.int/wp-content/uploads/2020/12/Turkcell_AI-for-Good_ML_in_5G_Challenge_2021.06.14.pdf 
Contact: aydin.cetin@turkcell.com.tr 
https://www.itu.int/en/ITU-T/AI/challenge/2020/Pages/Turkcell.aspx 
https://www.itu.int/en/ITU-T/AI/challenge/2020/Documents/ITU-AI-Challenge-Turkcell-RLF-Salih-Erg%c3%bct-v1.0.pdf 

63
Shared Experience Using 5G+AI (3D Augmented + Virtual Reality)
The 3D geoinformation research group is part of Section Urban Data Science , Delft University of Technology, and is affiliated with AMS, the Amsterdam Institute for Advanced Metropolitan Solutions.
The group focuses on technologies underpinning 3D geo-data and the integration with Building Information Models (BIMs) and aims at designing, developing, and implementing open data and open source solutions to model cities, buildings, and landscapes in 3D for environmental and urban studies. Open Science is an important principle of our research. We are also the main provider of education in the MSc Geomatics.
Shared Experience Using 5G+AI (3D Augmented + Virtual Reality)
Noise 3D:
https://3d.bk.tudelft.nl/opendata/noise3d/en.html 
3D city models:  https://3d.bk.tudelft.nl/opendata/opencities/ 
Other data:  https://3d.bk.tudelft.nl/opendata/ 

All the Data links are accessible using the above link.
Open-Source Projects:  https://3d.bk.tudelft.nl/code/ https://3d.bk.tudelft.nl/projects/  
Sample GitHub:
https://github.com/tudelft3d 
Liszio, Stefan & Masuch, Maic. (2016). Designing Shared Virtual Reality Gaming Experiences in Local Multi-platform Games. 10.1007/978-3-319-46100-7_23.

64
NETWORK TRAFFIC RECOGNITION AND PREDICTION BASED ON MACHINE LEARNING TECHNIQUES
The key feature of the proposal is to use the metadata of flows (fig 1.1, 1.2) on the data plane at the same time the analytical application with AI/ML algorithms is located on the service level and working with the SDN/NFV network via northbound APIs.
NETWORK TRAFFIC RECOGNITION AND PREDICTION BASED ON MACHINE LEARNING TECHNIQUES

https://github.com/alirefaee/ITU-AI-ML-IN-5G-CHALLENGE-SPbSUT/tree/master/dataset 

Data is accessible using the above link.
https://github.com/alirefaee/ITU-AI-ML-IN-5G-CHALLENGE-SPbSUT/tree/master/Presentation 
challenge link: http://itu-ai-challenge.sut.ru/ 
Khayyat, M., Elgendy, I. A., Muthanna, A., Alshahrani, A., Alharbi, S., & Koucheryavy, A. (2020). Advanced Deep Learning-based Computational Offloading for Multilevel Vehicular Edge-Cloud Computing Networks. IEEE Access, 1–1. https://doi.org/10.1109/access.2020.3011705

65
Improving experience and enhancing impressiveness of Video conferencing and collaboration
The database includes 420 videos that were evaluated by 65 subjects which led into 9750 continuous-time and 9750 retrospective subjective opinion scores. Continuous-time scores capture the instantaneous Quality of Experience (QoE), while retrospective scores reflect the overall viewing experience. These videos were generated from 15 video contents streamed under 7 different network conditions and 4 client adaptation strategies. These 7 network conditions are actual network traces from the HSDPA dataset representing challenging 3G mobile networks. The 4 client adaptation strategies cover the most representative client adaptation algorithms, such as rate-based, buffer-based and quality-based. The selected video contents cover a diverse set of content genres (action, documentary, sports, animation and video games). The content characteristics span a large variety including natural and animation video content, fast/slow motion scenes, light/dark scenes and low and high texture scenes.
Improving experience and enhancing impressiveness of Video conferencing and collaboration
https://docs.google.com/forms/d/e/1FAIpQLSewDvrgyPMq-iaW9n0n9MIvDU0KTNJXseD_EJug5a-Ntd7PQQ/viewform

Fill the above form to get the password to get access to datasets. 

https://utexas.app.box.com/v/LIVE-NFLX-Plus/

Click on the link and enter the password to get access to the datasets.

Contact:  cbampis@gmail.com
zli@netflix.com
amoorthy@netflix.com 
https://live.ece.utexas.edu/research/LIVE_NFLX_II/live_nflx_plus.html 
The purpose of this database is to study subjective QoE under very realistic streaming conditions, including the network conditions, the type of the streaming adaptation algorithm and the video content.
https://live.ece.utexas.edu/research/LIVE_NFLXStudy/nflx_index.html 
https://ieeexplore.ieee.org/document/9409699 

66
5G+ML/AI (Dynamic Spectrum Access)
Participants would be required to extract datafrom a simulated 5G environment and use it to demonstrate performance objectives defined by them.
5G+ML/AI (Dynamic Spectrum Access)
https://github.com/nyuwireless-unipd/ns3-mmwave

https://github.com/nyuwireless-unipd/ns3-mmwave
Participants would be required to extract data from a simulated 5G environment
5G-LENA: The 5G NR module for the ns-3 simulator:  https://5g-lena.cttc.es/ 
https://youtu.be/3tDyylZsPy4 
https://www.3gpp.org/release-17 
https://www.3gpp.org/dynareport?code=38-series.htm

67
Demonstration of MLFO capabilities via reference implementations
curated by Letterkenny Institute of Technology, Co. Donegal
Demonstration of MLFO capabilities via reference implementations
https://www.atu.ie/LYIT-ITU-T-AI-Challenge

Page not found. 
NA
NA
NA
68
Network state estimation by analysing raw video data
[path1] : Path to the directory containing the video data to be decomposed into frames. If there is more than one video data in the directory, process them all.
[path2] : The path to the directory that will output the frames decomposed by video. If the directory does not exist, a new one will be created.
Network state estimation by analysing raw video data
https://github.com/ITU-AI-ML-in-5G-Challenge/PS-031-NEC-Team-JOJO/tree/main/Data 

Data is accessible using the above link.
https://www.itu.int/en/ITU-T/AI/challenge/2020/Documents/PS-031-NEC_HENOKO_KING.pdf https://github.com/ITU-AI-ML-in-5G-Challenge/PS-031-NEC-Team-JOJO 
https://arxiv.org/pdf/2204.07062
https://deepai.org/publication/network-state-estimation-using-raw-video-analysis-vqos-gan-based-non-intrusive-deep-learning-approach  


GeoAI 2024 Challenges
69
GeoAI Ground-level NO2 Estimation
The data are:
Ground-truth data from air quality monitoring stations in the continental part of Lombardy and Veneto regions.
Remote sensing data of NO2 from Sentinel-5P TROPOMI, precipitation from CHIRPS and land surface temperature from NOAA datasets, all from Google Earth Engine (GEE).
Participants don't have to use all the parameters provided but are encouraged to create new ones from the existing ones, which could help to improve the performance of the model.
GeoAI Ground-level NO2 Estimation Challenge by ITU
https://zindi.africa/competitions/geoai-ground-level-no2-estimation-challenge/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
Sample GitHub Solution:
https://github.com/yash-raj202134/GeoAI-ground-level-NO2-estimation 
https://github.com/franfurey/itu_challenge_2024 
Launch of 2024 ITU GeoAI Challenge: https://youtu.be/C-82p-grs7w 
NA

70
GeoAI Agricultural Plastic Cover Mapping with Satellite Imagery
Limited number of training samples for plastic cover mapping, participants can also collect some training samples by themselves as cropland extent can be visually interpreted from Google Earth and Satellite images. It is notable that the training samples we are providing are collected by visually implement of satellite in April and May of each test region.
GeoAI Agricultural Plastic Cover Mapping with Satellite Imagery
https://zindi.africa/competitions/geoai-challenge-for-agricultural-plastic-cover-mapping-with-satellite-imagery/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
NA
NA

71
GeoAI Amazon Basin Secret Runway Detection
It is recommended the use of Sentinel-1 and Sentinel-2 images, which are considered particularly suitable for this challenge, leveraging both SAR and optical technologies. The data pre-processing methodology are not limited. The participants need to share the availability of the data they used and how the pre-processing is conducted. Sentinel data are freely available in a variety of platforms
GeoAI Amazon Basin Secret Runway Detection
https://zindi.africa/competitions/geoai-amazon-basin-secret-runway-detection-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
Sample GitHub Solution:
https://github.com/liangchow/zindi-amazon-secret-runway 

https://dataspace.copernicus.eu/ 

72
INEGI UN-GGIM Human Settlement Detection
The dataset for this challenge consists of satellite images collected from the Landsat series. The data has been pre-processed and divided into training and testing sets
The data has been labelled by in-situ field operations. Each row of the data corresponds to a 16x16 pixel patch extracted from a Landsat image. Each pixel patch has 6 spectral bands.
INEGI UN-GGIM Human Settlement Detection
https://zindi.africa/competitions/inegi-gcim-human-settlement-detection-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
Sample GitHub Solution: https://github.com/koleshjr/INEGI-UN-GGIM-Human-Settlement-Detection-Challenge-by-ITU/tree/main 
https://www.kaggle.com/code/tobby18/human-settlement-detection-challenge-by-itu 
GeoAI Challenges: Vegetation Mapping and Human Settlement Detection Challenge: https://youtu.be/9PeJ2HmnPtU 
NA

73
INEGI UN-GGIM Vegetation Mapping
You are provided with several sets of training data (tabular data); one with the values of remote sensing reflectance (year and dry season composites from Harmonized Landsat Sentinel imagery) as well as bioclimate data for precipitation and temperature, relief (elevation, slope, aspect, topographical position), canopy height among others, for each record in the training data set. A second set with the original noisy vegetation labels, and a third set with revised labels that can be used to improve the original data. This second data set (improved labels) has been thoroughly but NOT exhaustively checked, so it can also contain a number of wrong labels; so part of the challenge is to have a robust method to improve the training data.
The data provided correspond to one tile of the Mexican Geospatial Data Cube; about 150 Km by 150 Km, in the Pacific Coast of Mexico, almost centered in Puerto Vallarta. It contains a variety of ecosystems; going from tropical semidry to humid forests, as well as temperate forests, grasslands (cultivated and induced), mangroves and other wetlands, several types of agriculture and built-up areas.
INEGI UN-GGIM Vegetation Mapping
https://zindi.africa/competitions/inegi-gcim-vegetation-mapping-challenge/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
Sample GitHub Solution:
https://github.com/koleshjr/INEGI-UN-GGIM-Vegetation-Mapping-Challenge-by-ITU 
GeoAI Challenges: Vegetation Mapping and Human Settlement Detection Challenge: https://youtu.be/9PeJ2HmnPtU
NA

74
‘AIntuition’: Retrieval Augmented Generation (RAG) for Public Services and Administration
Retrieval Augmented Generation (RAG) plays a crucial role in enhancing the capabilities of Language Model (LLM) applications for public administration. LLM-powered virtual assistants need to efficiently access information from vast volumes of administrative and regulatory documents, which are frequently updated. Moreover, as primary aggregators of data, public institutions must seamlessly draw insights from their records to enhance user experiences for both employees and citizens. RAG is instrumental in fulfilling these functions by enabling LLM-powered virtual assistants to effectively query documents and provide accurate, contextually relevant responses.
‘AIntuition’: Retrieval Augmented Generation (RAG) for Public Services and Administration
https://zindi.africa/competitions/retrieval-augmented-generation-rag-for-public-services-and-administration-tasks/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.
https://aiforgood.itu.int/wp-content/uploads/2021/06/Slides_hackathon.pdf 
AIntuition: Unlocking Efficiency for Public Sector with Retrieval Augmented Generation Applications: https://youtu.be/Ck5adt-FJns 
https://digitallibrary.un.org/collection/Documents%20and%20Publications?ln=en 

https://www.afdb.org/en/all-documents 

https://infobrics.org/documents/ 

https://eur-lex.europa.eu/homepage.html 

75
ITU Digital Financial Services Blockchain Secure Authentication Application
To develop or submit an existing fully functional digital wallet application that is compatible with both web and mobile platforms, utilizing Password less BSA as the sole authentication method. Additionally, the same mobile application will serve as the application’s authenticator for Password less BSA.
ITU Digital Financial Services Blockchain Secure Authentication Application
https://zindi.africa/competitions/itu-digital-financial-services-blockchain-secure-authentication-application-challenge/data 

Data not provided
Data is not accessible

https://resourceaz.fnsbsa.com/itu-ac/resources/02-AC-aOS-SDK.pdf 
https://resourceaz.fnsbsa.com/itu-ac/resources/03-AC-Web-SDK.pdf
FCM Setting Guide:  https://resourceaz.fnsbsa.com/itu-ac/resources/08-AC-FCM-Setting-Guide.pdf 
https://resourceaz.fnsbsa.com/itu-ac/resources/04-AC-Provision-Server-Guide.pdf 

https://resourceaz.fnsbsa.com/fnspay/resources/02-FNSPay-Manual-Guide.pdf 


GeoAI 2023 Challenges
76
IDRISI-RE
GeoAI Challenge Location Mention Recognition from social media
IDRISI-R is the largest-scale publicly available Twitter Location Mention Recognition (LMR) dataset, The "R" refers to the recognition task. IDRISI-R contains 41 disaster events of different types (e.g., floods, earthquakes, fires, etc.) that occurred in a wide geographical area of the English- and Arabic-speaking countries across continents. The annotated LMs were also labeled for different coarse- (e.g., country, city) and fine-grained location types (e.g., streets, POIs).
GeoAI Challenge Location Mention Recognition from social media
Dataset: IDRISI-RE in json format https://github.com/rsuwaileh/IDRISI/tree/main/LMR/data/EN/gold-random-json
Data is accessible using the above link.
The full training, dev and test files, can be downloaded from here: https://github.com/rsuwaileh/IDRISI/blob/main/LMR/data/EN/gold-random-json/
https://github.com/rsuwaileh/IDRISI/tree/main/LMR/models 
https://github.com/rsuwaileh/IDRISI/tree/main/LMR 

https://github.com/moadel2002/Location-Mention-Recognition 

https://zindi.africa/competitions/geoai-challege-location-mention-recognition-from-social-media 
NA

77
GeoAI Challenge Estimating Soil Parameters from Hyperspectral Images
The dataset comprises 2886 patches in total (2 m GSD), of which 1732 patches for training and 1154 patches for testing. The patch size varies (depending on agricultural parcels) and is on average around 60x60 pixels. Each patch contains 150 contiguous hyperspectral bands (462-942 nm, with a spectral resolution of 3.2 nm), which reflects the spectral range of the hyperspectral imaging sensor deployed on-board Intuition-1.
GeoAI Challenge Estimating Soil Parameters from Hyperspectral Images
Train dataset : https://s3.waw2-1.cloudferro.com/swift/v1/AUTH_afccea586afd4ef3bb11fe37dd1ddfbf/Download_KPLabs_Chellenge/train_data.zip 

 Test dataset: https://s3.waw2-1.cloudferro.com/swift/v1/AUTH_afccea586afd4ef3bb11fe37dd1ddfbf/Download_KPLabs_Chellenge/test_data.zip 

Starter Toolkit: https://github.com/AI4EO/kp-labs-seeing-beyond-visible-challenge 

Data is accessible using the above link
https://zindi.africa/competitions/geoai-challenge-estimating-soil-parameters-from-hyperspectral-images/data  

Partners: https://www.qzsolutions.pl/ 

https://www.kplabs.space/ 

https://philab.esa.int/ 

78
GeoAI Challenge for Air Pollution Susceptibility Mapping
The discrete timeseries data of the pollution levels are provided from 2016 to 2021 in the metropolitan city of Milan, where the city of Milan is located. Additional data of factors that may influence the pollution levels are provided. The data has been preprocessed and the points are provided in a tabular format containing all the relevant data. The data includes meteorological timeseries, land cover maps, the digital terrain model, a geological map, the river distance, and other relevant data. The meteorological timeseries consists of discrete points.
The data available is:
Meteorological time series data (2016-2022) which includes temperature, precipitation, relative humidity, solar radiation, wind speed and direction at a daily temporal resolution.
Air pollution timeseries data (2016-2021) which includes NOx, SO2, CO, O3, PM2.5, PM10, and benzene at a daily temporal resolution.
Digital terrain model, land cover, geology, plan curvature, hill shade, slope, SPI, TRI, TWI are provided at the stations’ points and as a continuous representation at 100-m resolution.
GeoAI Challenge for Air Pollution Susceptibility Mapping
https://zindi.africa/competitions/geoai-challenge-for-air-pollution-susceptibility-mapping/data 

Data is accessible using the above link and you have to sign in and accept the terms to get the data.


Sample submissions https://github.com/ITU-GeoAI-Challenge/GeoAI-Challenge-Air-Pollution-Susceptibility-Mapping
https://github.com/ITU-GeoAI-Challenge/GeoAI-Challenge-for-Air-Pollution-Susceptibility-Mapping 
2023 ITU GeoAI Challenge Finale: Air Pollution Susceptibility Mapping: https://youtu.be/UX-_zCUFTMI 
Sample  presentation: https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2FITU-GeoAI-Challenge%2FGeoAI-Challenge-for-Air-Pollution-Susceptibility-Mapping%2Frefs%2Fheads%2Fmain%2FGeoAI%2520Air%2520Quality%2520Susepcitibility.pptx&wdOrigin=BROWSELINK 
"Reverse_geopy"library: https://geopy.readthedocs.io/en/stable/#nominatim 

Li, X., Li, D., & Shi, Y. (2017). A Comparative Study of Inverse Distance Weighting and Radial Basis Function Networks for Spatial Interpolation of Precipitation. ISPRS International Journal of Geo-Information, 6(6), 188. DOI: 10.3390/ijgi6060188. 

79
GeoAI Challenge for Cropland Mapping
1. Satellite images: the participants should use all free-accessible satellite data (e.g. Landsat, Sentienl-1/2) in the test regions, the data pre-processing methodology are not limited, either. We will provide 15-day composited Sentinel-2 time series data in the Iran and Sudan test regions. For the test region in Afghanistan, the participants will have to collect the imagery independently. The participants need to share the availability of the data they used and how the pre-processing is conducted, if they used more data than the official provided data set.
2. Training samples: We will provide a limited number of training samples for cropland mapping; participants can also collect some training samples by themselves as cropland extent can be visually interpreted from Google Earth and Satellite images. Particularly, for the cropland mapping in Afghanistan, training samples were collected in April 2022, and the model is used to identify cropland extent in the same period.
GeoAI Challenge for Cropland Mapping
https://zindi.africa/competitions/geo-ai-challenge-for-cropland-mapping-with-satellite-imagery/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Sample GitHub solution: https://github.com/ITU-GeoAI-Challenge/6th-Place-Cropland-Mapping 
https://github.com/ITU-GeoAI-Challenge/3rd_place_cropland_mapping 
2023 ITU GeoAI Challenge Finale: Cropland Mapping: https://youtu.be/NwNmgfWxAuM 
sample ppt: https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2FITU-GeoAI-Challenge%2F3rd_place_cropland_mapping%2Frefs%2Fheads%2Fmain%2FPresentation.pptx&wdOrigin=BROWSELINK 
[1] https://www.indexdatabase.de/db/is.php?sensor_id=168 
[2] https://www.indexdatabase.de/db/is.php?sensor_id=96 

80
GeoAI Challenge for Landslide Susceptibility Mapping
The datasets provided for the case study include:
1. a Digital Terrain Model (DTM) in a raster format at a 5 m/pixel scale (source: Lombardy Region),
2. training dataset (Train.gpkg) which is a combination of:
2.1. a landslide inventory comprising the boundaries of translational, rotational shallow landslides, and debris flows at a 1:10,000 scale in vector format. In the Train.gpkg has an assigned value of 1 in the “Target” field. (modified from source: ISPRA – Regione Lombardia. Inventario dei Fenomeni Franosi in Italia - IFFI).
2.2. No Landslide Zone - a vector layer depicting areas with low probability of shallow landslide occurrence at a 1:10,000 scale in vector format. The NLZ is computed using slope angle and lithology for the AOI. (source: GISGeolab@Politecnico di Milano). In the Train.gpkg has an assigned value of 0 in the “Target” field.
3. a road network at a 1:10,000 scale in vector format (source: Lombardy Region),
4. a river network at a 1:10,000 scale in vector format (source: Lombardy Region),
5. geological fault zones map at a 1:10,000 scale in vector format (source: Lombardy Region),
6. a land use/land cover map at a 1:10,000 scale in vector format (source: Lombardy Region),
7. Meteorological data:
7.1. Interpolated yearly averaged hour precipitation for the year of 2020 (source: ARPA Lombardia),
7.2. 90th percentile of the hour precipitation for the year of 2020 (source: ARPA Lombardia).
GeoAI Challenge for Landslide Susceptibility Mapping
https://zindi.africa/competitions/geo-ai-challenge-for-landslide-susceptibility-mapping/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Sample GitHub solutions: 
https://github.com/ITU-GeoAI-Challenge/Landslide_Susceptibility_Mapping 
https://github.com/ITU-GeoAI-Challenge/1st_place_Landslide_Susceptibility 
2023 ITU GeoAI Challenge Finale: Landslide Susceptibility Mapping: https://youtu.be/0iC2AZsov4I 
NA

81
Multi-Machine Disruption Prediction Challenge for Fusion Energy
Diverse dataset comprising approximately 1000 shots from J-TEXT, 1000 shots from HL-2A, and a limited number of shots from C-Mod, all provided in hdf5 format.
data from three distinct tokamaks, namely C-Mod, J-TEXT, and HL-2A. J-TEXT and HL-2A will be used as training set, and the C-Mod data set will be used for evaluation.

Multi-Machine Disruption Prediction Challenge for Fusion Energy
https://zindi.africa/competitions/multi-machine-disruption-prediction-challenge/data

Data is accessible using the above link and you have to sign in and accept the terms to get the data.

Sample GitHub solution: https://github.com/AI-for-Fusion-Energy/multi-machine-challenge-4th-place-Ning-Jia 
https://github.com/AI-for-Fusion-Energy/Multi-Machine_Nuclear_Fusion_Disruption 
AI for Fusion Energy Challenge Finale: Multi-Machine Disruption Prediction: https://youtu.be/OhjvBBuBBts  
https://pandas.pydata.org/docs/whatsnew/v1.5.3.html 
https://pypi.org/project/lightgbm/ 
https://scikit-learn.org/stable/whats_new/v1.2.html 
https://pypi.org/project/google/ 

82
Cropland mapping with satellite imagery
1.Satellite images: We will provide remote sensing dataset for each test region, and the data used for this challenge are limited to the official provided data. 2.Ground truth data: We will not provide specific ground truth samples for this group because the samples for cropland extent and crop intensity can be visually interpreted from Google Earth and Satellite images. 3.Legend of cropland extent and crop intensity.
Remote Sensing data: The 15-day composited Sentinel-2 data with 10m resolution are provided in geotiff format, the data are collected between July 2019 and June 2020. The data cover all the four test regions used in this challenge, and are available in both Google Drive and Google Earth Engine.
Cropland mapping with satellite imagery
https://drive.google.com/drive/folders/1cM0-LuCZA72DxSQslytundQnRGk5WyQD 

Data is accessible using the above link.

Sample GitHub solutions:
https://github.com/JuliusFx131/GEO-AI-Challenge-for-Cropland-Mapping-Challenge 
GEO-AI Challenge on Cropland mapping with satellite imagery: https://aiforgood.itu.int/wp-content/uploads/2020/12/Guideline-for-GEO-AI-challenge_0628.pdf 
NA

83
Location Mention Recognition from social media Crisis-related Text
The IDRISI-R dataset is used for development and evaluation in this challenge. It contains 19 disaster events with a total of 20,514 annotated tweets.
The data is available in JSONL format.
The data for every event has been split into training, development, and test sets.
Location Mention Recognition from social media Crisis-related Text
https://github.com/rsuwaileh/IDRISI/ 

Data is accessible using the above link.

Sample GitHub solution:
https://github.com/rsuwaileh/TLLMR4CM 
https://docs.docker.com/get-started/


84
School mapping with big data
School location data for Sudan

Satellite imagery for schools and non-school areas
School mapping with big data
https://github.com/dohyung-kim/GeoAI 

Data source is invalid.

Conatcs given:
Giga mapping/tech team: Dohyung Kim (dokim@unicef.org)  Iyke Maduako (imaduako@unicef.org)  Ivan Javier Dotu Rodriguez (jdoturodriguez@unicef.org) 
UNICEF Sudan Country Office: Rasha Obaid (robaid@unicef.org) 

https://geoaichallenge.aiforgood.itu.int/match/matchitem/62 
https://github.com/developmentseed/unicef-schools 
https://github.com/unicef/DS_school_detection/tree/tryolabs_main 
https://www.mdpi.com/2072-4292/14/4/897 
https://www.mdpi.com/2072-4292/13/15/2908 


Innovate for Impact 2024 Usecases
85
Hungary Simulation Tool
This is a data analytics platform providing downloadable datasets and insights on various economic and social indicators for Hungary. The tool offers comprehensive data downloads for research, policy-making, and strategic planning purposes.
1. Water resource management

2. Agricultural Sustainability

3. Climate Change Mitigation
https://hungary-simtool.herokuapp.com/SimulationDashBoard/models 
We can download the raw data from the above-mentioned link. 
The raw data includes Water, Energy, Social Inclusion.
SDG 11.6.1 measures the proportion of municipal solid waste collected and managed in controlled facilities, evaluating the efficiency of urban waste management through methods like recycling, energy recovery, and incineration. 
https://github.com/Global-Green-Growth-Institute/Hungury_ggsimtool 

The above link displays simulation results with two components: a simulation tool for policy modeling and an evidence library containing models, data, and codes.

1.https://ggindex-simtool.gggi.org/ 

2.https://www.abonyilab.com/ 

3.https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0300531 
 
86
Agmarknet and Open Data Telangana
The Agmarknet portal provides daily commodity price and arrival information for various agricultural products across different states in India.
The Telangana Open Data Portal provides datasets related to agriculture in Telangana, India. It includes information on crop production, weather patterns, irrigation, soil health, and agricultural schemes, aiming to promote data-driven decision making and enhance agricultural practices in the state.
1. AI based Chatbot for Farmers

2. Soil Health Prediction 

3. Crop Yield Prediction

4. Precision Farming Solutions
Machine Learning Algorithms (XGB Regression Model),
NLP, Geospatial analysis.

https://agmarknet.gov.in/PriceAndArrivals/CommodityDailyStateWise.aspx 

https://data.telangana.gov.in/

The above-mentioned platforms have datasets which can be downloaded and to use to train the models. 
https://iasri.icar.gov.in/
https://iiss.icar.gov.in/about%20iiss.html
https://mausam.imd.gov.in/ https://mkisan.gov.in/ 
There are 4 Indian platforms mentioned, all of them aim to support Indian agriculture through technology, research, and advisory services, focusing on improving productivity, sustainability, and farmer welfare.
https://bsssjournals.onlinelibrary.wiley.com/doi/10.1111/ejss.13413 
 
87
Mapbox 
Traffic Data
Mapbox Traffic Sample Data provides a comprehensive dataset of real-time and historical traffic information, enabling developers to build and test traffic-aware applications. This sample data includes GPS trajectories, traffic incidents, and congestion metrics for various locations worldwide.
The Mapbox Traffic Sample Data page provides access to traffic datasets that showcase Mapbox's capabilities in visualizing real-time and historical traffic patterns. It allows developers and analysts to integrate traffic data into mapping applications, enabling insights into congestion trends, route optimization, and urban mobility analysis.
1. AI enabled Power efficient Macro Radio Unit

2. Public Transport Planning

3. AI enabled Route Optimization 
https://www.mapbox.com/forms/traffic-sample-data

From the mentioned platform you can download and access Mapbox Traffic Sample Data. In-order to access you must fill in the form and be able to get the data.

https://www.mapbox.com/forms/traffic-sample-data

Time series data analysis, CPU utilization monitoring, Optimization Strategies, 5G NR.

1.https://www.sciencedirect.com/science/article/pii/S2405959522000996

2.https://ieeexplore.ieee.org/document/8663985 
  
88
Measuring Gross Carbon Dioxide Emissions from Forest Fires in the Abrace o Pantanal Project Area
Consists of early detection and monitoring of wildfires using high-resolution cameras and satellite data, aided by the Pantera platform, which facilitates communication and the mobilization of firefighting brigades. The project covers 2.5 million hectares of the Pantanal biome, with five cameras installed in the Serra do Amolar region, an area severely affected by wildfires in 2020.
Embrace the Forest
https://www.dropbox.com/scl/fo/cvdcl0ljfmpxw6c2hrhoo/AOFqAf5f3l_0ynPLBZtqawA?rlkey=0723zx7473twiozumsv2sqc96&e=1&dl=0
https://uplink.weforum.org/uplink/s/uplink-contribution/a012o00001pU1zEAAS/Preventing%20wildfires%20to%20mitigate%20CO2%20emissions 
https://embracetheforest.umgrauemeio.com/ 
https://revistas.uniandes.edu.co/index.php/nys/issue/view/613

https://revistas.uniandes.edu.co/index.php/nys/article/view/1151 
1.https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_02_Ch2_Generic.pdf

2.https://doi.org/10.53010/nys5.02
 
89
Public GPS Traces
OpenStreetMap provides map data for thousands of websites, mobile apps, and hardware devices. It is built by a community of mappers that contribute and maintain data about roads, trails, cafés, railway stations, and much more, all over the world.
AI enabling travel model helps search and resuce incidental lost elderly people for the global ageing challenge
Metadata: Structured and Unstructured data, AI models for training the data.

Refer to usecase no. 39 in [4]
https://www.openstreetmap.org/traces
https://www.openstreetmap.org/communities

1.https://arxiv.org/abs/2206.15005 

2.https://arxiv.org/abs/2303.13047 
 
90
Roboflow Computer Vision Datasets
Roboflow hosts free public computer vision datasets in many popular formats (including CreateML JSON, COCO JSON, Pascal VOC XML, YOLO v3, and Tensorflow TFRecords). Role-based Access Ensure privacy and security for your data by giving each user in Roboflow specific access based on their role within the computer vision pipeline. Control which users can assign images for labeling, train models, access datasets, and utilize the labeling tools for annotation. 
Computer Network Fusion Video Brain
https://public.roboflow.com/

https://public.roboflow.com/object-detection

https://huggingface.co/datasets


https://github.com/QwenLM/Qwen-VL

https://arxiv.org/pdf/1506.02640 

 
91
LAION-5B: DATASETS
A New Era of open large-scale multi-modal. Large image-text models like ALIGN, BASIC, Turing Bletchly, FLORENCE & GLIDE have shown better, and better performance compared to previous flagship models like CLIP and DALL-E. The motivation behind dataset creation is to democratize research and experimentation around large-scale multi-modal model training and handling of uncurated, large-scale datasets crawled from publically available internet.
Vivo’s Technology for All: Bridging the accessibility Gap
Internal company data, User-authorized data, Generated data, https://wukong-dataset.github.io/wukong-dataset/index.html

https://github.com/ksOAn6g5/TaiSu


https://openreview.net/pdf?id=iAxH-ikIP0I

 

ITU WTSA-24 Hackathon Usecases

92
AI CITY CHALLENGE
CityFlow: a city-scale multi-camera vehicle tracking dataset proposed by Tang, et. al (2019). The datasets are available through the AI City Challenge (2021). Our team has requested access to the dataset by filling out this form, we expect to start model development as soon as our request has been granted. 2. OpenWeatherMap API: To get access to weather conditions we use the API. 3. PredictHQ’s API: We’ll use the API to get access to events in a city to enhance our traffic flow estimation algorithm. 
Traffic Optimization 
and Urban Mobility
Traffic prediction and dynamic signal optimization.

https://openweathermap.org/api

https://www.predicthq.com/events/upcoming-events

https://github.com/Nkosana-263/AI-Mavericks-Traffic-Optimisation

1.https://arxiv.org/abs/1903.09254

2.https://arxiv.org/abs/2104.12233

3.https://arxiv.org/abs/2004.14619 
 
93
Construction Dataset Computer Vision Project
This Dataset consists of Images from classes: cables, person, building structure, pile casing, bore pile, piling rig, car, etc.
An ecosystem for measuring Forensic Delay Analysis
Anomaly Detection, Visual Sentiment Analysis – Image Classification, Risk Identification, Forensic Delay Analysis, [GenAI] Image Captioning of Construction Site Images, [GenAI] Prompts for Intent Classification of Site Activity.
https://universe.roboflow.com/klinterai/construction-dataset-6xih3/dataset/3 
https://github.com/KlinterAI/klinterai-website

https://klinterai-tenant.vercel.app/

https://klinterai.carrd.co/

1.https://www.sciencedirect.com/science/article/pii/S2666827021000670
2.https://paperswithcode.com/area/computer-vision 

94
SkyScenes Dataset and UAVVaste Dataset
SkyScenes datasets are Synthetic Dataset for Aerial Scene Understanding and UAVVaste Dataset is for Autonomous, Onboard Vision-Based Trash and Litter Detection in Low Altitude Aerial Images Collected by an Unmanned Aerial Vehicle
Eyes from Above - “Waste Accumulation”: Scheduled UAV visits
Classification Algorithms, Deep convolutional neural networks
https://arxiv.org/abs/2312.06719#:~:text=Sahil%20Khose,%20Anisha%20Pal,%20Aayushi%20Agarwal
https://github.com/Ram5anthosh/WTSA2024

https://www.mdpi.com/2072-4292/13/5/965 
1.https://indiawris.gov.in/downloads/Ganga%20Basin.pdf
2.https://link.springer.com/chapter/10.1007/978-981-99-1588-0_32 


ITU Kaleidoscope 2024 Presentations

95
Plant Village Dataset
Potato Plant Leaf Disease Detection Using Custom CNN Deep Net: A Step Towards Sustainable Agriculture. This dataset consists of 3 classes viz. late_blight, early_blight and healthy. The dataset contains 1000 images for the diseased classes and 152 images for the healthy leaves. To address the data imbalance problem the healthy category data are augmented and increased to 1000 samples. These 3000 samples were used to train the classifiers. Further, for detection 64 images after augmentation and annotation.
Potato Plant Leaf Disease Detection Using Custom CNN Deep Net: A Step Towards Sustainable Agriculture
Models implemented are:
	•	Customized 5-layer
	•	2. CNN 4-layer 
	•	3. CNN Mobilenet
Detection model: Faster R-CNN used for detecting potato leaf diseases. 
5-layer CNN best model (97.16 accuracy) 
Detected 3 categories: Early Blight, Late Blight, Healthy leaves.


N/A
https://www.itu.int/en/ITU-T/academia/kaleidoscope/2024/Documents/S1.2Potato%20Plant%20Leaf%20Disease%20Detection%20Using%20Custom%20CNN%20Deep%20Net%20A%20Step%20Towards%20Sustainable%20Agriculture.pdf 

96
Wildchat public dataset
A system for privacy-preserving insights into real-world AI use
Clio: Privacy-Preserving Insights into Real-World AI Use
https://www.anthropic.com/research/clio?ref=platformer.news

https://arxiv.org/abs/2405.01470
 N/A
https://assets.anthropic.com/m/7e1ab885d1b24176/original/Clio-Privacy-Preserving-Insights-into-Real-World-AI-Use.pdf 

97
[1] 3D City Model (Project PLATEAU)
[2] 3D City Model (Project PLATEAU) Chiyoda Ward (FY2023)
The data is from "PLATEAU Open Data 3D Urban Model Chuo-ku[1] and Chiyoda-ku[2]” (Ministry of Land, Infrastructure, Transport and Tourism, Japan). The offered data is created by a file format conversion.
This is a 3D city model in which features such as buildings are generated in 3D from data acquired based on aerial surveys. Anyone can use it freely free of charge, including commercial use.
KDDI AIforGood webinar – Dec 2024
https://www.geospatial.jp/ckan/dataset/plateau-13102-chuo-ku-2023

https://www.geospatial.jp/ckan/dataset/ 

https://www.geospatial.jp/ckan/dataset/plateau-13101-chiyoda-ku-2023
N/A
https://www.mlit.go.jp/plateau/ 

98
ECOTOX effect
Semanticwebtechnologiesenabletheinteroperabilityofdisparatedatasources.Wehavecreatedaknowledgegraph. based on major data sources used in ecotoxicological risk assessment. These facilities the use of the extensive library of semantic webtools. We have applied this knowledge graph to aim portant task in risk assessment, namely chemical effect prediction. Our extensive evaluation shows that byusing knowledge graph embeddings we can increase the accuracy of effect prediction overa. Simple baseline. Furthermore, we have implemented a fine-tuning architecture which adapts the knowledge graph embeddings to the effect prediction task and leads to a better performance.
Prediction of Adverse Biological Effects of Chemicals Using Knowledge Graph Embeddings
N/A
https://github.com/turing-knowledge-graphs/teaching/tree/main/city 
https://www.semantic-web-journal.net/system/files/swj2658.pdf 

99
Fall detection dataset from Kaggle
Some wearables proposed are able to detect trips and slips but not specifically fall. So, cStick, a calm stick to monitor falls in older adults is proposed. cStick has been designed in such a way that it can assist both visually and hearing-impaired older adults. cStick has an ability to not only detect falls but to also predict the incident of fall so as to reduce their occurrences. cStick can monitor the surroundings, warn the user if there was a previous fall detected at a certain location, and update the location and its surroundings to the user.
Elderly Wellness Companion with Voice and Video-Based Health Anomaly Detection
https://www.kaggle.com/datasets/laavanya/elderly-fall-prediction-and-detection

ITU-T FG-AI4H Deliverable, Voice based CNN system, Real time data.


N/A
https://ieeexplore.ieee.org/abstract/document/10772962  

100
Human fetal brain
The Indian Institute of Technology Madras (IIT-Madras) has unveiled the world's largest collection of high-resolution 3D images of the human fetal brain. The dataset, dubbed DHARANI, includes 5,132 brain sections captured at cellular resolution with the help of advanced brain mapping technology.

https://www.unicef.org/india/key-data#:~:text=With%20the%20birth%20of%2025,the%20world's%20annual%20child%20births

https://ai4bharat.iitm.ac.in/datasets  
https://brainportal.humanbrain.in/publicview/index.html 
This is the dataset
https://pib.gov.in/PressReleasePage.aspx?PRID=2082652 


UN Pet Guide

101
European Statistical System Data
Sensor data was collected from survey participants' smart devices.
Enhancing traditional surveys with real-time data from smart devices, ensuring privacy through federated learning.
TensorFlow Federated (for Federated Learning)
https://ec.europa.eu/eurostat/cros/content/essnet-smart-surveys_en https://doi.org/10.1017/dap.2020.7 https://europa.eu/!DjbbHw https://europa.eu/!FU98Jt
Smith, J., & Doe, J. (2020). "Federated Learning for Privacy-Preserving Data Analysis." Journal of Privacy and Confidentiality.

https://ec.europa.eu/eurostat/cros/content/eurostat-cybernetica-project_en


102
Eurostat Mobile Network Operator Data
Daily visited locations by individual subscribers from mobile network operators.
Analyzing mobility patterns while preserving user privacy using Trusted Execution Environments (TEEs).
Intel SGX (for Trusted Execution Environments)
https://ec.europa.eu/eurostat/cros/content/eurostat-cybernetica-project_en
Brown, D., & White, M. (2019). "Trusted Execution Environments for Secure Data Processing." IEEE Security & Privacy.

https://ec.europa.eu/eurostat/cros/content/eurostat-cybernetica-project_en

 
103
Indonesian Mobile Network Operator Data
IMSIs from two mobile network operators.
Generating accurate tourism statistics by analyzing cross-roaming data without compromising individual privacy.
Sharemind (for Secure Multi-Party Computation)
https://sharemind.cyber.ee/sharemind-hi/
 https://netmob.org/assets/netmob19_withFCC.pdf 
Santoso, A. (2018). "Secure Multi-Party Computation for Tourism Statistics." International Journal of Data Science.

N/A.
 
104
Italian Socio-Demographic and Financial Data
Socio-demographic and financial data from ISTAT and Bank of Italy.
Enhancing socio-economic analysis by securely linking datasets from different sources.
R and Python libraries (for Privacy-Preserving Record Linkage)
N/A
Rossi, M., & Bianchi, L. (2021). "Privacy-Preserving Record Linkage: Methods and Applications." Statistical Journal of the IAOS.

https://www.isi-web.org/files/docs/papers-and-abstracts/56-day2-ips047-input-privacy-towards-a-logica.pdf

 
105
UK Census Data
UK Census data, linked census-mortality data, Covid Infection Survey.
Testing engineering and analytical pipelines using synthetic data to ensure privacy and data utility.
Synthpop (for Synthetic Data Generation)
2021 Census Dress Rehearsal Using GANs to create synthetic data SynthGauge python package for evaluating synthetic data
Johnson, E. (2022). "Synthetic Data Generation for Privacy-Preserving Analysis." Journal of Official Statistics.

https://www.isi-web.org/files/docs/papers-and-abstracts/56-day2-ips047-input-privacy-towards-a-logica.pdf

 
106
Samsung SDS Data Aggregation System
Randomly generated datasets of various sizes.
Demonstrating secure data aggregation without a trusted third party using Secure Multi-Party Computation (SMPC).
MP-SPDZ (for Secure Multi-Party Computation)
N/A
Kim, H. (2020). "Secure Multi-Party Computation in Data Aggregation." Journal of Cryptographic Engineering.
Maliciously Secure Matrix Multiplication with Applications to Private Deep Learning
 
107
Statistics Canada Data Coverage Measurement
Synthetic data generated from public census data.
Measuring the coverage of third-party data sources relative to NSO data, ensuring privacy through exact data matching.
PSI-Toolkit (for Private Set Intersection)
[1] Christen, P. (2012). Data Matching, Berlin:Springer.

[2] Dasylva, A. and Goussanou, A. (2020). “Estimating linkage errors under regularity conditions”, Proceedings of the Survey Methods Section, American Statistical Association.

Brown, D. (2021). "Private Set Intersection for Data Coverage Measurement." Journal of Privacy and Confidentiality.

https://arxiv.org/abs/2106.07229

 
108
Statistics Canada Product Description Data
Synthetic product description data.
Ensuring input privacy while training machine learning models in a cloud environment.
Microsoft SEAL (for Homomorphic Encryption)
Z. Zanussi, B. Santos and S. Molladavoudi, Supervised text classification with leveled homomorphic encryption, To appear in the proceedings of the 63rd ISI World Statistics Congress, 2021.
Slides from UN ML Group presentation

Brown, D. (2021). "Homomorphic Encryption for Privacy-Preserving Machine Learning." Journal of Machine Learning Research.

https://arxiv.org/abs/2106.07229
 
109
Statistics Canada Synthetic Data for Training
Linked datasets from the 2006 long-form Census, Canadian Mortality Registry, Canadian Cancer Registry, and Vital Statistics Death Database.
Providing high-quality synthetic data for training and hackathons, preserving privacy while maintaining analytical value.
Various cryptographic libraries (for Secure Multi-Party Computation)
Toward more user-centric data access solutions: Producing synthetic data of high analytical value by data synthesis - IOS Press
Brown, D. et al. (2021). "Private Set Intersection: A Comprehensive Guide."

https://arxiv.org/abs/2106.07229

 
110
Statistics Korea Data Hub Platform
Various kinds of data, including statistical registers.
Securely linking dispersed government data using state-of-the-art cryptographic techniques to develop a privacy-preserving statistical data hub.
PySyft and TensorFlow Federated (for Federated Learning)
N/A
Lee, M.-J. (2019). "Cryptographic Techniques for Privacy-Preserving Data Hubs." Journal of Information Security.

N/A
 
111
Statistics Netherlands Healthcare Data
Vertically partitioned healthcare data.
Developing risk prediction models from sensitive healthcare data while ensuring privacy.
PSI-Toolkit (for Private Set Intersection)
https://commit2data.nl/projecten/carrier
van der Meer, P. (2020). "Federated Learning for Healthcare Data Analysis." Journal of Medical Internet Research.

https://doi.org/10.48550/arXiv.2301.06167

 
112
Statistics Netherlands eHealth Solution Data
Medical data, treatment cost data, socio-economic data.
Measuring the effectiveness of eHealth solutions without sharing patient information.
PySyft (for Differential Privacy and Federated Learning)
https://www.cbs.nl/nl-nl/corporate/2021/37/succesvolle-pilot-cbs-tno-cz-en-zuyderland-analyse-van-data-op-afstand
https://www.cz.nl/over-cz/nieuws/praktijktest-succesvol
https://www.tno.nl/nl/over-tno/nieuws/2021/9/eerste-gemeenschappelijke-analyse-zonder-onderlinge-datadeling/ https://gitlab.com/ppa-project
https://medium.com/applied-mpc/secure-and-private-statistics-with-distributed-paillier-8a186410b5af https://www.linksight.nl/en/projects/ppa/

van der Meer, P. (2021). "Private Set Intersection in eHealth Solutions." Health Informatics Journal.

https://doi.org/10.48550/arXiv.2301.06167
 
113
Twitter and OpenMined Data
Data from the paper "Algorithmic Amplification of Politics on Twitter" and synthetic reproductions.
Evaluating the efficacy of PETs for algorithmic transparency and enabling privacy-preserving research.
PySyft and Microsoft SEAL (for Federated Learning and Homomorphic Encryption)
Announcing our Partnership with Twitter to Advance Algorithmic Transparency
Investing in privacy enhancing tech to advance transparency in ML

Algorithmic Amplification of Politics on Twitter
Christchurch Call Initiative on Algorithmic
Outcomes https://www.christchurchcall.com/media-and-resources/news-and-updates/

christchurch-call-initiative-on-algorithmic-outcomes/
Christchurch Call Initiative on Algorithmic Outcomes https://www.amcham.co.nz/page-1334006/12928098

Green, A. (2021). "Differential Privacy and Federated Learning for Algorithmic Transparency." Proceedings of the Privacy Enhancing Technologies Symposium.

https://docsend.com/view/db577xmkswv9ujap?submissionGuid=650e684f-93eb-4cee-99e8-12a92d5d88a0

 
114
UNECE Human Activity Recognition Data
Publicly available human activity recognition data.
Developing machine learning models on isolated data using federated learning and homomorphic encryption.
PySyft and PyTorch (for Secure Multi-Party Computation and Differential Privacy)
 Private ML track

White, M. (2020). "Federated Machine Learning for Privacy-Preserving Data Analysis." Journal of Big Data.

https://www.isi-web.org/files/docs/papers-and-abstracts/56-day2-ips047-input-privacy-towards-a-logica.pdf

 

Other Sources
115
Anthropic HH-RLHF dataset for model alignment
The data contain content that may be offensive or upsetting. Topics include, but are not limited to, discriminatory language and discussions of abuse, violence, self-harm, exploitation, and other potentially upsetting subject matter. Please only engage with the data in accordance with your own personal risk tolerance. The data are intended for research purposes, especially research that can make models less harmful. The views expressed in the data do not reflect the views of Anthropic or any of its employees.
Anthropic HH-RLHF dataset for model alignment
https://github.com/anthropics/hh-rlhf

Data is accessible using the above link.
NA
https://arxiv.org/abs/2204.05862 

https://arxiv.org/abs/2209.07858 


116
MIMIC-III for healthcare
MIMIC-III (‘Medical Information Mart for Intensive Care’) is a large, single-center database comprising information relating to patients admitted to critical care units at a large tertiary care hospital. Data includes vital signs, medications, laboratory measurements, observations and notes charted by care providers, fluid balance, procedure codes, diagnostic codes, imaging reports, hospital length of stay, survival data, and more. The database supports applications including academic and industrial research, quality improvement initiatives, and higher education coursework.
MIMIC-III for healthcare
https://static-content.springer.com/esm/art%3A10.1038%2Fsdata.2016.35/MediaObjects/41597_2016_BFsdata201635_MOESM102_ESM.zip 

Data is accessible using the above link.
https://www.nature.com/articles/sdata201635
https://www.nature.com/articles/sdata201635#MOESM102 

https://www.nature.com/articles/sdata201635.pdf 



117
MIMIC-IV, a freely accessible electronic health record dataset
Digital data collection during routine clinical practice is now ubiquitous within hospitals. The data contains valuable information on the care of patients and their response to treatments, offering exciting opportunities for research. Typically, data are stored within archival systems that are not intended to support research. These systems are often inaccessible to researchers and structured for optimal storage, rather than interpretability and analysis. Here we present MIMIC-IV, a publicly available database sourced from the electronic health record of the Beth Israel Deaconess Medical Center. Information available includes patient measurements, orders, diagnoses, procedures, treatments, and deidentified free-text clinical notes. MIMIC-IV is intended to support a wide array of research studies and educational material, helping to reduce barriers to conducting clinical research.
MIMIC-IV, a freely accessible electronic health record dataset
https://www.nature.com/articles/s41597-022-01899-x

https://www.nature.com/articles/s41597-022-01899-x
https://mimic.mit.edu/
https://github.com/MIT-LCP/mimic-code/ 
https://mimic.mit.edu/docs/gettingstarted/ 
https://www.nature.com/articles/s41597-022-01899-x.pdf 

118
CodeSearchNet for coding
CodeSearchNet is a collection of datasets and benchmarks that explore the problem of code retrieval using natural language. This research is a continuation of some ideas presented in this blog post and is a joint collaboration between GitHub and the Deep Program Understanding group at Microsoft Research - Cambridge.
CodeSearchNet for coding
https://github.com/github/CodeSearchNet 

Data is accessible using the above link.
https://github.com/github/CodeSearchNet/blob/master/notebooks/ExploreData.ipynb 
https://arxiv.org/abs/1909.09436 

https://www.microsoft.com/en-us/research/project/deep-program-understanding/ 


119
Crop Recommendation Dataset
Dataset helps the farmers to get informed decision about the farming strategy. Dataset which would allow the users to build a predictive model to recommend the most suitable crops to grow in a particular farm based on various parameters.

AI enabled soil analysis weather station for local farmers
https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset 

The above link is accessible. You have to sign in to Kaggle and can be able to download the data.

This dataset is recommended to us by our partner in CSIR Ghana. 
Sample notebooks:
https://www.kaggle.com/code/moazeldsokyx/crop-recommendation-with-machine-learning 
https://www.kaggle.com/code/arpitamallik23/crop-recommendation-system-99 
https://aurora.portal.csem.ch/ 

120
Harvard Law School Data.gov Archive

To download an individual dataset by name you can construct its URL.
data.gov includes multiple kinds of datasets, including some that link to actual data files, such as CSV files, and some that link to HTML landing pages. Our process runs a "shallow crawl" that collects only the directly linked files. Datasets that link only to a landing page will need to be collected separately.
Harvard Law School Data.gov Archive

https://source.coop/harvard-lil/gov-data/collections/data_gov/fruit-and-vegetable-prices/v1.zip

https://source.coop/harvard-lil/gov-data/metadata/data_gov/fruit-and-vegetable-prices/v1.json 

Data is accessible using the above link.
https://source.coop/repositories/harvard-lil/gov-data/description
https://lil.law.harvard.edu/blog/tag/tools/ 
GitHub: https://github.com/harvard-lil/data-vault 

https://case.law/

https://lil.law.harvard.edu/century-scale-storage/

https://lil.law.harvard.edu/blog/2025/02/06/announcing-data-gov-archive/ 

121
M3Exam - World Knowledge in Regional Languages
M3Exam is a collection of real-life and native official human exam question benchmarks. This benchmark covers questions from multiple countries in the SEA region, which require strong multilingual proficiency and cultural knowledge across various critical educational periods, from primary- to high-school levels of difficulty.
M3Exam - World Knowledge in Regional Languages
https://drive.google.com/file/d/1eREETRklmXJLXrNPTyHxQ3RFdPhq_Nes/view

Data is accessible using the above link.
https://github.com/DAMO-NLP-SG/M3Exam
https://github.com/DAMO-NLP-SG/DAMO-SeaLLMs?tab=readme-ov-file

https://arxiv.org/pdf/2306.05179 

https://arxiv.org/abs/2009.03300 

refer to usecase-12 in innovate for impact report [4]


