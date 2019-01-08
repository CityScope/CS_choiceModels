model ABM

global {
	// FILES
	file geojson_zones <- file("../includes/geoIdsGAMA.geojson");
	file geojson_roads <- file("../includes/bostonRoads1234.geojson");
	file geojson_grid <- file("../includes/bostonGrid2x2.geojson");
	file occat_1_pop <- file("../includes/pop_occat_1.csv"); // populations to sample workers  of each type from from 
	file occat_2_pop <- file("../includes/pop_occat_2.csv");
	file occat_3_pop <- file("../includes/pop_occat_3.csv");
	file occat_4_pop <- file("../includes/pop_occat_4.csv");
	file occat_5_pop <- file("../includes/pop_occat_5.csv");
	matrix occat_1_mat <- matrix(occat_1_pop);
	matrix occat_2_mat <- matrix(occat_2_pop);
	matrix occat_3_mat <- matrix(occat_3_pop);
	matrix occat_4_mat <- matrix(occat_4_pop);
	matrix occat_5_mat <- matrix(occat_5_pop);
//	file shape_file_bounds <- file("../includes/bounds.shp");
	geometry shape <- envelope(geojson_zones);
	float step <- 10 #sec;
//	int nb_people <- 100;
	date starting_date <- date("2018-7-01T06:00:00+00:00");
//	int current_hour update: (time / #hour) mod 24;
	// PARAMETERS
	//TODO  need to update logic of trip timing based on data
	int current_hour update: 6 + (time / #hour) mod 24;
	int min_work_start <- 6;
	int max_work_start <- 8;
	int min_work_end <- 16; 
	int max_work_end <- 20; 
	int occat_1<-0; // number of new workers of each type introduced in the interacion zone (due to new commercial space).
	int occat_2<-0;
	int occat_3<-0;
	int occat_4<-0;
	int occat_5<-0;
	int res_00<-0; // capacity of new residences of each type in the  interaction zone
	int res_01<-0;
	int res_02<-0;
	int res_10<-0;
	int res_11<-0;
	int res_12<-0;
	int res_20<-0;
	int res_21<-0;
	int res_22<-0;
	list res_available<-[res_00, res_01, res_02, res_10, res_11, res_12, res_20, res_21, res_22];
	// remaining capacity for each residence type in interaction zone
	
	// INDICATORS
	list res_needed<-[0,0,0,0,0,0,0,0,0];
	// unmet demand for eah residence type in the interaction zone ( for pie chart)
	map<string,int> modal_split <- map(['car', 'bike', 'walk', 'PT'] collect (each::0));
	
	map<string,rgb> color_per_mobility <- ["car"::#red, "bike"::#blue, 'walk'::#green, 'PT'::#yellow];
	map<string,int> speed_per_mobility <- ["car"::20, "bike"::10, 'walk'::5, 'PT'::15];
	
	list nm_occats<-[occat_1, occat_2, occat_3, occat_4, occat_5];
	list occat_mats<-[occat_1_mat, occat_2_mat, occat_3_mat, occat_4_mat, occat_5_mat];
//	list sampled_occat_1<-sample(range(0,1000,1),occat_1, false); // should use length of file

	graph the_graph;
	
	init {
		// create graph, zones and buildings (interaction zone)
		write 'init';
		create road from: geojson_roads;
		the_graph <- as_edge_graph(road);
		create buildings from: geojson_grid;
		create zones from: geojson_zones with: [zoneId::string(read ("id"))];
		
		// create the new people spawned from the new workplaces
		loop o from: 0 to:length(nm_occats)-1{ // do for each occupation category
			if (nm_occats[o]>0){
				loop i from: 0 to: nm_occats[o]{ // create N people
	//				write occat_1_mat[4, i];
					create people {	
						resType<-occat_mats[o][8, i]; // get nth res type from the appropriate csv file
						age<-occat_mats[o][4, i];
						hh_income<-occat_mats[o][0, i];
						motif<-occat_mats[o][7, i];
						education<-occat_mats[o][1, i];
						life_cycle<-occat_mats[o][2, i];
						if (res_available[resType]>0){
							home_location<-any_location_in (one_of(buildings));
							res_available[resType]<-res_available[resType]-1;
						}
						//TODO better choice of home zone
						else {
							home_location<-any_location_in (one_of(zones));
							res_needed[resType]<-res_needed[resType]+1;
						}
		          		work_location<-any_location_in (one_of(buildings));
		          		location<-home_location;
						start_work <- min_work_start + rnd (max_work_start - min_work_start) ;
		          		end_work <- min_work_end + rnd (max_work_end - min_work_end) ;
		          		objective <- "resting";	          		
					}
				}			
			}			
		}
		
		// Create the baseline population according to census data
		create people from:csv_file( "../includes/agents.csv",true) with:
			[home_zone_num::int(get("o")), 
			work_zone_num::int(get("d")),
			mode::string(get("mode"))
			]{
				home_location<-any_location_in (zones[home_zone_num]);
				work_location<-any_location_in (zones[work_zone_num]);
				location<-home_location;
				start_work <- min_work_start + rnd (max_work_start - min_work_start) ;
          		end_work <- min_work_end + rnd (max_work_end - min_work_end) ;
          		objective <- "resting"; 
          		do set_speed_color;
          		modal_split[mode] <- modal_split[mode]+1;
          		modeSet<-true;      		
			}
	}	
}

species zones {
	string zoneId; 
	rgb color <- #gray  ;
	
	aspect base {
		draw shape color: color ;
	}
}

species road  {
	rgb color <- #white ;
	
    aspect base {
	draw shape color: color ;
	}
}

species buildings {
	string type<-nil;
	int capacity<-0;
	int available<-0;
	rgb color <- #white  ;
	
	aspect base {
		draw shape color: color ;
	}
}

species people skills:[moving] {
	rgb color <- #black ;
	int resType<-0;
	string mode<-nil;
	int hh_income<-6;
	int home_zone_num<-0;
	int work_zone_num<-0;
	int age<-40;
	string motif<-'HWH';
	int education<-4;
	int life_cycle<-5;
	point home_location<-nil;
	point work_location<-nil;
//	zones home_zone <- nil;
//	zones work_zone <- nil;
//	int profile <- 0;
	int start_work ;
	int end_work  ;
	string objective ; 
	point the_target <- nil ;
	float distance;
	bool modeSet<-false;
	
	aspect base {
		draw circle(30) color: color;
	}
	
	reflex set_mode when: modeSet=false{
		// TODO should happen for each trip when entire motif is modelled
		using topology(the_graph){
		     distance <- distance_to (home_location,work_location);
		}
		do choose_mode(distance,motif, age, life_cycle);
		do set_speed_color;
		modeSet<-true;
	}
	reflex time_to_work when: current_hour = start_work and objective = "resting"{
		objective <- "working" ;
		the_target <- work_location;
//		float distance<-0.0;
//		using topology(the_graph){
//		     distance <- distance_to (location,the_target);
//		}
//		do choose_mode(distance,'HWH', age, life_cycle);
//		do set_speed_color;
	}
		
	reflex time_to_go_home when: current_hour = end_work and objective = "working"{
		objective <- "resting" ;
		the_target <- home_location;
//		float distance<-distance_to(location,the_target);
//		do choose_mode(distance,'HWH', age, life_cycle);
//		do set_speed_color;
	} 
	 
	reflex move when: the_target != nil {
		do goto target: the_target on: the_graph ; 
		if the_target = location {
			the_target <- nil ;
		}
	}
	
	action choose_mode(float trip_leg_meters, string motif, int age, int education) {
		// based on the calibrated Decision Trees (java script produced in python)
		if (trip_leg_meters <= 531.53) { 
         if (trip_leg_meters <= 149.21) { 
             if (education <= 1.50) { 
                 if (hh_income <= 7.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.6, 0.0, 0.3, 0.1])];} 
                else {// if hh_income > 7.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.06, 0.25, 0.62, 0.06])];} 
                }
            else {// if education > 1.50 
                 if (age <= 66.00) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.08, 0.0, 0.92, 0.0])];} 
                else {// if age > 66.00 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.18, 0.0, 0.82, 0.0])];} 
                }
            }
        else {// if trip_leg_meters > 149.21 
             if (motif !='HOOH') { 
                 if (age <= 65.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.26, 0.03, 0.71, 0.0])];} 
                else {// if age > 65.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.62, 0.0, 0.38, 0.0])];} 
                }
            else {// if motif_HOOH > 0.50 
                 if (trip_leg_meters <= 375.95) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.44, 0.06, 0.5, 0.01])];} 
                else {// if trip_leg_meters > 375.95 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.78, 0.0, 0.18, 0.04])];} 
                }
            }
        }
    else {// if trip_leg_meters > 531.53 
         if (trip_leg_meters <= 1220.24) { 
             if (age <= 44.00) { 
                 if (education <= 4.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.57, 0.02, 0.31, 0.1])];} 
                else {// if education > 4.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.27, 0.23, 0.48, 0.03])];} 
                }
            else {// if age > 44.00 
                 if (motif != 'HWH') { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.82, 0.01, 0.16, 0.01])];} 
                else {// if motif_HWH > 0.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.5, 0.0, 0.5, 0.0])];} 
                }
            }
        else {// if trip_leg_meters > 1220.24 
             if (motif != 'HWWH') { 
                 if (age <= 43.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.84, 0.01, 0.03, 0.12])];} 
                else {// if age > 43.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.95, 0.01, 0.02, 0.03])];} 
                }
            else {// if motif_HWWH > 0.50 
                 if (age <= 67.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.77, 0.0, 0.04, 0.19])];} 
                else {// if age > 67.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.0, 0.0, 0.0, 1.0])];} 
                }
            }
        }
        modal_split[mode] <- modal_split[mode]+1;
    }
	
	
	action set_speed_color{
		// can this be done using a 'case' syntax?
		if mode='car'{
			speed<-20.0 #km/#h;
			color<-#red;
		}
		else if mode='bike'{
			speed<-10.0 #km/#h;
			color<-#blue;
		}
		else if mode='PT'{
			speed<-15.0 #km/#h;
			color<-#yellow;
		}
		else{
			speed<-5.0 #km/#h;
			color<-#green;
		}
	}
		
}


experiment mobilityAI type: gui {
	parameter "Sales jobs" var: occat_1 category: "New Jobs" min: 0 max: 50;
	parameter "Clerical jobs" var: occat_2 category: "New Jobs" min: 0 max: 50;
	parameter "Manufacturing jobs" var: occat_3 category: "New Jobs" min: 0 max: 50;
	parameter "Professional jobs" var: occat_4 category: "New Jobs" min: 0 max: 50;
	parameter "Student Enrollments" var: occat_5 category: "New Jobs" min: 0 max: 50;
	parameter "Res 1 Bed Low Rent" var: res_00 category: "New Housing" min: 0 max: 50;
	parameter "Res 1 Bed Medium Rent" var: res_01 category: "New Housing" min: 0 max: 50;
	parameter "Res 1 Bed High Rent" var: res_02 category: "New Housing" min: 0 max: 50;
	parameter "Res 2 Bed Low Rent" var: res_10 category: "New Housing" min: 0 max: 50;
	parameter "Res 2 Bed Medium Rent" var: res_11 category: "New Housing" min: 0 max: 50;
	parameter "Res 2 Bed High Rent" var: res_12 category: "New Housing" min: 0 max: 50;
	parameter "Res 3 Bed Low Rent" var: res_20 category: "New Housing" min: 0 max: 50;
	parameter "Res 3 Bed Medium Rent" var: res_21 category: "New Housing" min: 0 max: 50;
	parameter "Res 3 Bed High Rent" var: res_22 category: "New Housing" min: 0 max: 50;
	output {
		display housing{
			chart "Housing Demand" type:pie {
				data "Res 1 Bed Low Rent" value:res_needed[0] color:rgb(166,206,227);
				data "Res 1 Bed Medium Rent" value:res_needed[1] color:rgb(178,223,138);
				data "Res 1 Bed High Rent" value:res_needed[2] color:rgb(51,160,44);
				data "Res 2 Bed Low Rent" value:res_needed[3] color:rgb(251,154,153);
				data "Res 2 Bed Medium Rent" value:res_needed[4] color:rgb(227,26,28);
				data "Res 2 Bed High Rent" value:res_needed[5] color:rgb(253,191,111);
				data "Res 3 Bed Low Rent" value:res_needed[6] color:rgb(31,120,180);
				data "Res 3 Bed Medium Rent" value:res_needed[7] color:rgb(255,127,0);
				data "Res 3 Bed High Rent" value:res_needed[8] color:rgb(202,178,214);
			}			
		}
		display modes{
			chart "Modal Split" background:#white type: pie  
				{
					loop i from: 0 to: length(modal_split.keys)-1	{
					  data modal_split.keys[i] value: modal_split.values[i] color:color_per_mobility[modal_split.keys[i]];
					}
				}			
		}
		display city_display type:opengl {
			species zones aspect: base ;
			species road aspect: base ;
			species buildings aspect: base ;
			species people transparency:0.2 aspect: base ;
			overlay position: { 3,3 } size: { 120 #px, 140 #px } background: # gray transparency: 0.8 border: # black 
            {	
            		draw string(current_date.hour) + "h" + string(current_date.minute) +"m" at: { 20#px, 30#px } color: # black font: font("Helvetica", 25, #italic) perspective:false;
  				draw "Mobility Modes" at: { 20#px, 60#px } color: #black font: font("Helvetica", 15, #bold) perspective:false;
  				draw "Car" at: { 20#px, 75#px } color: #red font: font("Helvetica", 15, #bold ) perspective:false;
  				draw "Bike" at: { 20#px, 90#px } color: #blue font: font("Helvetica", 15, #bold ) perspective:false;
  				draw "Public Transit" at: { 20#px, 105#px } color: #yellow font: font("Helvetica", 15, #bold ) perspective:false;
  				draw "Walk" at: { 20#px, 120#px } color: #green font: font("Helvetica", 15, #bold ) perspective:false;
            }
//			graphics "time" {
//				draw string(current_date.hour) + "h" + string(current_date.minute) +"m" color: # black font: font("Helvetica", 25, #italic) at: {world.shape.width*0.9,world.shape.height*0.55};
//			}
		
				
			}
		
		
	}
}