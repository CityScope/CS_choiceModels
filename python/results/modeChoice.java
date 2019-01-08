def predictModeProbs(){ 
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
             if (motif_HOOH <= 0.50) { 
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
                 if (motif_HWH <= 0.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.82, 0.01, 0.16, 0.01])];} 
                else {// if motif_HWH > 0.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.5, 0.0, 0.5, 0.0])];} 
                }
            }
        else {// if trip_leg_meters > 1220.24 
             if (motif_HWWH <= 0.50) { 
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
    }
