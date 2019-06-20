# ofdm_demodulator class 
# Last modification by initentity generator 
#Simple buffer template

import os
import sys
import numpy as np
import tempfile

from thesdk import *
from verilog import *
from verilog.testbench import *
from verilog.testbench import testbench as vtb

class ofdm_demodulator(verilog,thesdk):
    #Classfile is required by verilog and vhdl classes to determine paths.
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,*arg): 
        self.proplist = [ 'Rs' ];    # Properties that can be propagated from parent
        self.Rs =  100e6;            # Sampling frequency
        self.IOS=Bundle()
        self.IOS.Members['A'] = IO();               # Pointer for input data
        _=verilog_iofile(self,name='A', dir='in', ionames=['io_A_real', 'io_A_imag' ])

        self.IOS.Members['symbol_sync_in'] = IO();  # Pointer for input data
        _=verilog_iofile(self,name='symbol_sync_in', dir='in', ionames=['io_symbol_sync_in'])

        self.IOS.Members['symbol_sync_out'] = IO(); # Pointer for input data
        _=verilog_iofile(self,name='symbol_sync_out', dir='out', 
                ionames=['io_symbol_sync_out'] ) 
        
        self.IOS.Members['Z'] = IO();              # Pointer for output data
        _=verilog_iofile(self,
                name='Z', dir='out', ionames=['io_Z_real', 'io_Z_imag'], datatype='scomplex' )
        self.IOS.Members['control_write']= IO() 
        # This is a placeholder, file is created elsewher
        #_=verilog_iofile(self, name='control_write', dir='in', iotype='file') 
        self.model='py';             # Can be set externally, but is not propagated
        self.par= False              # By default, no parallel processing
        self.queue= []               # By default, no parallel processing

        if len(arg)>=1:
            parent=arg[0]
            self.copy_propval(parent,self.proplist)
            self.parent =parent;
        self.init()

    def init(self):
        pass
        #This gets updated every time you add an iofile
        ##self.iofile_bundle=Bundle()
        # Define the outputfile

    def main(self):
        data=self.IOS.Members['A'].Data
        syncindex=np.where(self.IOS.Members['symbol_sync_in'].Data==1)[0]
        #[TODO]Fasten by memory pre-allocation
        for i in range(syncindex.shape[0]):
            if i==0:
                received=data[syncindex[i]:syncindex[i]+64].reshape(1,-1)
            elif syncindex[i]+64<data.shape[0]:
                received=np.r_['0', received, \
                        data[syncindex[i]:syncindex[i]+64].reshape(1,-1)
                    ]
        ft=np.fft.fft(received[:,0:64],axis=1)
        ft2=np.r_['1', ft,np.zeros((ft.shape[0],16),dtype=complex)]
        syncout=np.zeros(ft2.shape)
        syncout[:,0]=1
        self.IOS.Members['symbol_sync_out'].Data=syncout.reshape(-1,1)
        self.IOS.Members['Z'].Data=ft2.reshape(-1,1)
        if self.par:
            self.queue.put(self.IOS.Members['Z'].Data)
            self.queue.put(self.IOS.Members['symbol_sync_out'].Data)

    def run(self,*arg):
        if len(arg)>0:
            self.par=True      #flag for parallel processing
            self.queue=arg[0]  #multiprocessing.queue as the first argument
        if self.model=='py':
            self.main()
        elif self.model=='sv':
            self.vlogparameters=dict([ ('g_Rs',self.Rs),])
            self.run_verilog()

            #This is for parallel processing
            if self.par:
              self.queue.put(out)
            #Large files should be deleted
            del self.iofile_bundle

        elif self.model=='vhdl':
            self.print_log(type='F', msg='VHDL model not yet supported')

    def define_io_conditions(self):
        # Input A is read to verilog simulation after 'initdo' is set to 1 by controller
        for name, val in self.iofile_bundle.Members.items():
            if val.dir is 'in':
                self.iofile_bundle.Members[name].verilog_io_condition='initdone'
        # Output is read to verilog simulation when all of the utputs are valid, 
        # and after 'initdone' is set to 1 by controller
            if val.dir is 'out':
                self.iofile_bundle.Members[name].verilog_io_condition_append(
                        cond='&& initdone')
                if val.name is 'Z':
                    self.iofile_bundle.Members[name].verilog_io_condition_append(
                            cond='\n&& ~$isunknown(io_symbol_sync_out)')




if __name__=="__main__":
    import matplotlib.pyplot as plt
    from  ofdm_demodulator import *
    from  ofdm_demodulator.controller  import controller \
            as ofdm_demodulator_controller
    from signal_generator_802_11n import *
    import pdb
    symbol_length=64
    Rs=20e6
    signal_generator=signal_generator_802_11n()
    signal_generator.Rs=Rs
    signal_generator.Users=1
    signal_generator.Txantennas=1
    bbsigdict_ofdm_sinusoid3={ 
            'mode':'ofdm_sinusoid', 
            'freqs':[1.0e6 , 3e6, 7e6 ], 
            'length':2**14, 
            'BBRs':20e6 
        };

    signal_generator.bbsigdict=bbsigdict_ofdm_sinusoid3
    signal_generator.ofdm_sinusoid()
    scale=np.amax(np.r_[signal_generator._Z.Data[0,0,:].real, \
            signal_generator._Z.Data[0,0,:].imag])
    data=np.round((signal_generator._Z.Data[0,0,:]/scale)\
            .reshape(-1,1)*(2**10-1))
    symbol_sync=np.zeros((data.shape[0],1))
    offset=8
    symbol_sync[offset::80,0]=1
    controller=ofdm_demodulator_controller()
    controller.reset()
    controller.step_time(step=10*controller.step)
    controller.start_datafeed()
    duts=[ ofdm_demodulator() for i in range(2)]
    duts[1].model='sv'
    toplot=[]
    for d in duts:    
        d.Rs=Rs
        d.init()
        #d.interactive_verilog=True
        d.interactive_verilog=False
        d.IOS.Members['A'].Data=data.reshape(-1,1)
        d.IOS.Members['symbol_sync_in'].Data=symbol_sync.astype('int')
        d.IOS.Members['control_write']=controller.IOS.Members['control_write']
        d.run()
        syncindex=np.where(d.IOS.Members['symbol_sync_out'].Data.astype('int')==1)[0]
        for i in range(syncindex.shape[0]):
            if i==0:
                received=d.IOS.Members['Z'].Data[syncindex[i]:syncindex[i]+64].reshape(1,-1)
            elif syncindex[i]+64<d.IOS.Members['Z'].Data.shape[0]:
                received=np.r_['0', received, \
                        d.IOS.Members['Z'].Data[syncindex[i]:syncindex[i]+64].reshape(1,-1)]
        toplot.append(received)

    #Plots start here
    f0=plt.figure(0)
    x_ref=np.arange(64).reshape(-1,1) 
    plt.plot(x_ref,np.abs(toplot[0][0,:]),x_ref,np.abs(toplot[0][40,:]))
    plt.xlim(0,63)
    plt.suptitle("Python model")
    plt.xlabel("Bin")
    plt.ylabel("Symbol")
    plt.grid()
    plt.show(block=False)
    f0.savefig('python_spectrum.eps', format='eps', dpi=300);

    f1=plt.figure(1)
    plt.plot(x_ref,data.real[offset:offset+64])
    plt.xlim(0,63)
    plt.suptitle("Python model")
    plt.xlabel("Bin")
    plt.ylabel("Symbol")
    plt.grid()
    plt.show(block=False)
    f1.savefig('python_time_domain.eps', format='eps', dpi=300);

    f2=plt.figure(2)
    plt.plot(np.abs(toplot[1][0,:]))
    plt.xlim(0,63)
    plt.suptitle("Verilog model")
    plt.xlabel("Bin")
    plt.ylabel("Symbol")
    plt.grid()
    plt.show(block=False)
    f2.savefig('verilog_spectrum.eps', format='eps', dpi=300);
    input()
