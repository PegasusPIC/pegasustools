import numpy as np
import pegasus_read as pegr
import pegasus_computation as pegc
import math

#output range [t(it0),t(it1)]--(it0 and it1 included)
it0 = 210      # initial time index
it1 = 258      # final time index

# box parameters
betai03 = 0.3
aspct = 6
lprp = 10.*np.sqrt(betai03)              # in (2*pi*d_i) units
lprl = lprp*aspct       # in (2*pi*d_i) units 
Lperp = 2.0*np.pi*lprp  # in d_i units
Lpara = 2.0*np.pi*lprl  # in d_i units 
N_perp = 200          
N_para = N_perp*aspct   # assuming isotropic resolution 
kperpdi0 = 1./lprp      # minimum k_perp ( = 2*pi / Lperp) 
kparadi0 = 1./lprl      # minimum k_para ( = 2*pi / Lpara)

#number of k_perp shells
nkshells = 138          # number of shells in k_perp--roughly: sqrt(2)*(N_perp/2)
kprp_min = kperpdi0     
kprp_max = nkshells*kprp_min#/2.0  
kprl_min = kparadi0
kprl_max = N_para*kprl_min/2.0

#files path
prob = "turb"
path = "../fig_data/beta03/rawdata_E_npy/"#"../joined_npy/"
path_out = "../fig_data/beta03/rawdata_E_npy/"#"../joined_npy/"


for ind in range(it0,it1+1):
  flnmE1 = path+"E1."+"%05d"%ind+".npy"
  flnmE2 = path+"E2."+"%05d"%ind+".npy"
  flnmE3 = path+"E3."+"%05d"%ind+".npy"  
  print "\n Reading files: \n"
  print " -> ",flnmE1
  E1 = np.load(flnmE1)
  print " -> ",flnmE2
  E2 = np.load(flnmE2)
  print " -> ",flnmE3
  E3 = np.load(flnmE3)

  phi = pegc.compute_potential(E1,E2,E3,N_para,N_perp,N_perp,kprl_min,kprp_min,kprp_min)

  flnm_save = path_out+"PHItot."+"%05d"%ind+".npy"
  np.save(flnm_save,phi)
  print " * Phi saved in -> ",flnm_save


