/* Implements crc4, taken from AN520
www.meas-spec.com/Workarea/DownloadAsset.aspx?id=8856
*/

#include <stdio.h>

unsigned char crc4(unsigned int n_prom[])
{
  int cnt; // simple counter
  unsigned int n_rem; // crc reminder
  unsigned int crc_read; // original value of the crc
  unsigned char n_bit;
  n_rem = 0x00;
  crc_read=n_prom[7]; //save read CRC
  n_prom[7]=(0xFF00 & (n_prom[7])); //CRC byte is replaced by 0

  for (cnt = 0; cnt < 16; cnt++) // operation is performed on bytes
    {// choose LSB or MSB
    if (cnt%2==1) n_rem ^= (unsigned short) ((n_prom[cnt>>1]) & 0x00FF);
    else n_rem ^= (unsigned short) (n_prom[cnt>>1]>>8);
    for (n_bit = 8; n_bit > 0; n_bit--)
    {
      printf("s: %04x\n", n_rem);
      if (n_rem & (0x8000))
      {
        n_rem = (n_rem << 1) ^ 0x3000;
      }
      else
      {
        n_rem = (n_rem << 1);
      }
    }
    printf("n_rem: %04x\n", n_rem);
  }
  n_rem= (0x000F & (n_rem >> 12));
  // final 4-bit reminder is CRC code
  n_prom[7]=crc_read;
  // restore the crc_read to its original place
  return (n_rem ^ 0x0);
}

int main(int argc, char** argv)
{
  unsigned int nprom[] = {0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500};
  unsigned int crc = crc4(nprom);
  printf("crc: %02x\n", crc);
  return 0;
}
