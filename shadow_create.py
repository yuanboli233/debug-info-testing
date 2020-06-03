import sys

def get_print_stmt(t: str, v: str) -> str:
    mapping = {
            'char':'c',
            'char*':'s',
            'short':'dh',
            'int':'d',
            'long':'dl',
            'unsigned short':'uh',
            'unsigned int':'u',
            'unsigned long':'ul',
            'float':'f',
            'double':'f',
            'long double':'Lf'
    }
    return 'printf("%{}", {});\n'.format(mapping[t], v)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        sys.exit('Usage: python3 {} <srcfile> <dstfile> <type> <varname> <line>'.format(sys.argv[0]))
    sf, df, t, v, l = sys.argv[1:6]
    with open(sf, 'r') as sf_handle:
        lines = sf_handle.readlines()
        lines.insert(int(l) - 1, get_print_stmt(t, v))
    with open(df, 'w') as df_handle:
        df_handle.write(''.join(lines))
