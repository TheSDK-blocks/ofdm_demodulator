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
        self.A = IO();               # Pointer for input data
        self.symbol_sync_in = IO();  # Pointer for input data
        self._symbol_sync_out = IO(); # Pointer for input data
        self.model='py';             # Can be set externally, but is not propagated
        self.par= False              # By default, no parallel processing
        self.queue= []               # By default, no parallel processing
        self._Z = IO();              # Pointer for output data
        if len(arg)>=1:
            parent=arg[0]
            self.copy_propval(parent,self.proplist)
            self.parent =parent;
        self.init()

    def init(self):
        #This gets updated every time you add an iofile
        ##self.iofile_bundle=Bundle()
        # Define the outputfile
        _=verilog_iofile(self,name='Z',datatype='complex')
        _=verilog_iofile(self,name='A',dir='in')
        _=verilog_iofile(self,name='symbol_sync_in',dir='in')
        _=verilog_iofile(self,name='symbol_sync_out')
        self.vlogparameters=dict([ ('g_Rs',self.Rs),])

    def main(self):
        data=self.A.Data
        syncindex=np.where(self.symbol_sync_in.Data==1)[0]
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
        self._symbol_sync_out.Data=syncout.reshape(-1,1)
        self._Z.Data=ft2.reshape(-1,1)
        if self.par:
            self.queue.put(self._Z.Data)
            self.queue.put(self._symbol_sync_out.Data)

    def run(self,*arg):
        if len(arg)>0:
            self.par=True      #flag for parallel processing
            self.queue=arg[0]  #multiprocessing.queue as the first argument
        if self.model=='py':
            self.main()
        elif self.model=='sv':
            self.control_write.Data.Members['control_write'].adopt(parent=self)

            # Create testbench and execute the simulation
            self.define_testbench()
            self.tb.export(force=True)
            self.write_infile()
            self.run_verilog()
            self.read_outfile()
            self._Z.Data=self.iofile_bundle.Members['Z'].data
            self._symbol_sync_out.Data=self.iofile_bundle\
                    .Members['symbol_sync_out'].data
            #This is for parallel processing
            if self.par:
              self.queue.put(out)
            #Large files should be deleted
            del self.iofile_bundle

        elif self.model=='vhdl':
            self.print_log(type='F', msg='VHDL model not yet supported')

    def write_infile(self):
        #Connect IOfiles here
        self.iofile_bundle.Members['A'].data=self.A.Data.reshape(-1,1)
        self.iofile_bundle.Members['symbol_sync_in'].data\
                =self.symbol_sync_in.Data.reshape(-1,1)
        # This could be a method somewhere
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='in':
                self.iofile_bundle.Members[name].write()

    def read_outfile(self):
        # Procedure: 
        # Define dtypes if not default
        # Sequence through the outfile
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                self.iofile_bundle.Members[name].read()

    # Testbench definition method
    def define_testbench(self):
        #Initialize testbench
        self.tb=vtb(self)
        # Create TB connectors from the control file
        for connector in self.control_write\
                .Data.Members['control_write'].verilog_connectors:
            self.tb.connectors.Members[connector.name]=connector
            # Connect them to DUT
            try: 
                self.dut.ios.Members[connector.name].connect=connector
            except:
                pass

        # Dut is created automaticaly, if verilog file for it exists
        self.tb.connectors.update(bundle=self.tb.dut_instance.io_signals.Members)

        #Assign verilog simulation parameters to testbench
        self.tb.parameters=self.vlogparameters

        # Copy iofile simulation parameters to testbench
        for name, val in self.iofile_bundle.Members.items():
            self.tb.parameters.Members.update(val.vlogparam)

        # Define the iofiles of the testbench. '
        # Needed for creating file io routines 
        self.tb.iofiles=self.iofile_bundle

        #Define testbench verilog file
        self.tb.file=self.vlogtbsrc


        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.tb.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='\'b0'

        # IO file connector definitions
        # Define what signals and in which order and format are read form the files
        # i.e. verilog_connectors of the file
        # All connectors should be already defined at this phase
        name='control_write'
        ionames=[ _.name for _ in self.control_write.Data.Members[name]\
                .verilog_connectors ]
        self.iofile_bundle.Members[name].verilog_connectors=\
                self.tb.connectors.list(names=ionames)
        
        #for name in ionames:
        #    self.tb.connectors.Members[name].type='signed'

        name='A'
        ionames=[]
        ionames+=['io_A_real', 'io_A_imag' ]
        self.iofile_bundle.Members[name].verilog_connectors=\
                self.tb.connectors.list(names=ionames)
        self.iofile_bundle.Members[name].verilog_io_condition='initdone'

        name='symbol_sync_in'
        ionames=[]
        ionames+=['io_symbol_sync_in']
        self.iofile_bundle.Members[name].verilog_connectors=\
                self.tb.connectors.list(names=ionames)
        self.iofile_bundle.Members[name].verilog_io_condition='initdone'

        name='Z'
        ionames=[]
        ionames+=['io_Z_real', 'io_Z_imag' ] 
        self.iofile_bundle.Members[name].verilog_connectors=\
                self.tb.connectors.list(names=ionames)

        self.iofile_bundle.Members[name].verilog_io_condition_append(\
                cond='&& initdone \n&& ~$isunknown(io_symbol_sync_out)' )
        for name in ionames:
            self.tb.connectors.Members[name].type='signed'

        name='symbol_sync_out'
        ionames=[]
        ionames+=['io_symbol_sync_out'] 
        self.iofile_bundle.Members[name].verilog_connectors=\
                self.tb.connectors.list(names=ionames)

        self.iofile_bundle.Members[name].verilog_io_condition_append(\
                cond='&& initdone')
        ## This method is in verilog_testbench class
        self.tb.generate_contents()

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
        d.A.Data=data
        d.symbol_sync_in.Data=symbol_sync
        d.control_write=controller.control_write
        d.run()
        syncindex=np.where(d._symbol_sync_out.Data.astype('int')==1)[0]
        for i in range(syncindex.shape[0]):
            if i==0:
                received=d._Z.Data[syncindex[i]:syncindex[i]+64].reshape(1,-1)
            elif syncindex[i]+64<d._Z.Data.shape[0]:
                received=np.r_['0', received, \
                        d._Z.Data[syncindex[i]:syncindex[i]+64].reshape(1,-1)]
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
