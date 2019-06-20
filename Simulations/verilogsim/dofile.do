add wave -position insertpoint  \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_A_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_A_imag \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_symbol_sync_in \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_symbol_sync_out \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_Z_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/io_Z_imag \
sim:/tb_ofdm_demodulator/ofdm_demodulator/serpa_0_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/serpa_1_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/serpa_62_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/serpa_63_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_in_bits_0_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_in_bits_1_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_in_bits_62_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_in_bits_63_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_out_bits_63_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT_io_out_sync \
sim:/tb_ofdm_demodulator/ofdm_demodulator/parse_0_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/parse_1_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/parse_62_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/parse_63_real \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT/DirectFFT_io_in_valid \
sim:/tb_ofdm_demodulator/ofdm_demodulator/FFT/DirectFFT_io_in_bits_0_real \

run -all

