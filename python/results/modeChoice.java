def predictModeProbs(){ 
     if (trip_leg_meters <= 1370.51) { 
         if (age <= 49.50) { 
             if (trip_leg_meters <= 517.73) { 
                 if (age <= 29.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.03, 0.54, 0.42, 0.02])];} 
                else {// if age > 29.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.05, 0.07, 0.88, 0.0])];} 
                }
            else {// if trip_leg_meters > 517.73 
                 if (education <= 4.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.1, 0.42, 0.25, 0.23])];} 
                else {// if education > 4.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.03, 0.82, 0.14, 0.02])];} 
                }
            }
        else {// if age > 49.50 
             if (trip_leg_meters <= 625.52) { 
                 if (education <= 1.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.06, 0.0, 0.23, 0.82])];} 
                else {// if education > 1.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.12, 0.0, 0.88, 0.0])];} 
                }
            else {// if trip_leg_meters > 625.52 
                 if (trip_leg_meters <= 1220.77) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.43, 0.0, 0.53, 0.05])];} 
                else {// if trip_leg_meters > 1220.77 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.78, 0.0, 0.0, 0.26])];} 
                }
            }
        }
    else {// if trip_leg_meters > 1370.51 
         if (age <= 32.50) { 
             if (motif_HOOH <= 0.50) { 
                 if (motif_HOH <= 0.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.18, 0.0, 0.04, 0.78])];} 
                else {// if motif_HOH > 0.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.57, 0.0, 0.1, 0.35])];} 
                }
            else {// if motif_HOOH > 0.50 
                 if (age <= 22.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([1.0, 0.0, 0.06, 0.0])];} 
                else {// if age > 22.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.42, 0.0, 0.03, 0.58])];} 
                }
            }
        else {// if age > 32.50 
             if (motif_HWWH <= 0.50) { 
                 if (education <= 4.50) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.62, 0.09, 0.07, 0.22])];} 
                else {// if education > 4.50 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.31, 0.33, 0.07, 0.29])];} 
                }
            else {// if motif_HWWH > 0.50 
                 if (trip_leg_meters <= 2770.76) { 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.47, 0.0, 0.93, 0.0])];} 
                else {// if trip_leg_meters > 2770.76 
                    mode<-['car', 'bike', 'walk', 'PT'][rnd_choice([0.09, 0.0, 0.0, 0.92])];} 
                }
            }
        }
    }
