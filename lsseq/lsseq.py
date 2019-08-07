#!/usr/bin/env python 
# lsseq
"""
Filter utility to condense long lists including identical or sequential lines
of text (such as the names of files in a PNG stream).
"""
import sys, re

def main(inp=sys.stdin):
    """
    Given a list of strings or lines from a stream, return a reduced
    list showing strings of duplicated lines or lines in an incrementing
    or decrementing sequence (like a PNG-stream):
    
    >>> sample = '''\
    ... S1E01-PC-1-Cam1-f00001.png
    ... S1E01-PC-1-Cam1-f00002.png
    ... S1E01-PC-1-Cam1-f00103.png
    ... S1E01-PC-1-Cam1-f00103.png
    ... S1E01-PC-1-Cam1-f00103.png
    ... S1E01-PC-1-Cam1-f00104.png
    ... S1E01-PC-1-Cam1-f00105.png
    ... S1E01-PC-1-Cam1-f00106.png
    ... S1E01-PC-1-Cam1-f00107.png
    ... S1E01-PC-1-Cam1-f00108.png
    ... S1E01-PC-1-Cam1-f02000.png
    ... S1E01-PC-1-Cam1-f02300.png
    ... S1E01-PC-1-Cam1-f02400.png
    ... S1E01-PC-1-Cam1-f02399.png
    ... S1E01-PC-1-Cam1-f02398.png
    ... S1E01-PC-1-Cam1-f02397.png
    ... S1E01-PC-1-Cam1-f02396.png
    ... S1E01-PC-1-Cam1-f03555.png
    ... S1E01-PC-1-Cam2-f03333.png
    ... S1E01-PC-1-Cam2-f03440.png
    ... S1E01-PC-1-Cam2-f03441.png
    ... '''
    >>> print(main(sample.split('\n')))
    S1E01-PC-1-Cam1-f00001.png
    S1E01-PC-1-Cam1-f00002.png
    
    S1E01-PC-1-Cam1-f00103.png
       x 3

    S1E01-PC-1-Cam1-f00104.png
       ... (5) +
    S1E01-PC-1-Cam1-f00108.png
    
    S1E01-PC-1-Cam1-f02000.png
    
    S1E01-PC-1-Cam1-f02300.png
    
    S1E01-PC-1-Cam1-f02400.png
       ... (5) -
    S1E01-PC-1-Cam1-f02396.png

    S1E01-PC-1-Cam1-f03555.png
    S1E01-PC-1-Cam2-f03333.png
    
    S1E01-PC-1-Cam2-f03440.png
    S1E01-PC-1-Cam2-f03441.png
    
    >>> 
    """
    listing=[]
    prev = None
    dup_run = 0
    inc_run = 0
    dec_run = 0
    #for line in inp:
    inp_iter = iter(inp)
    while 1:
        try:
            line = inp_iter.next()
        except StopIteration:
            line = None
            
        if prev is None:
            # first line
            prev = line
            base = line
            continue
             
        if line:
            comparison = compare_lines(prev, line)
        else:
            comparison = '!='
        
        if comparison == '==':
            dup_run += 1
        elif comparison == '+1' and not dup_run and not dec_run:
            inc_run += 1
        elif comparison == '-1' and not dup_run and not inc_run:
            dec_run += 1
        else:
            listing.append('')
            listing.append(base)       
            if dup_run:
                # Report # of duplicates and reset
                listing.append('   x {0:d}'.format(dup_run+1))
                
            elif inc_run==1 or dec_run==1:
                # If a listing is only 2 lines, then just list them
                listing.append(prev)
                
            elif inc_run>1:
                # Show range of increment run
                listing.append('   ... ({0:d}) +'.format(inc_run+1))
                listing.append(prev)
                
            elif dec_run>1:
                # Show range of decrement run
                listing.append('   ... ({0:d}) -'.format(dec_run+1))
                listing.append(prev)
            else:
                # Next file is unmatched ('!=') to previous
                pass
            dup_run = 0
            inc_run = 0
            dec_run = 0
            base = line
        if not line:
            # final iteration
            break
        prev=line
    return('\n'.join(listing))
       

numfield = re.compile(r'(^\d+)')
othfield = re.compile(r'(^\D+)')
def breakdown(s):
    """
    Break a string down into numerical fields delimited by non-numerical fields:
    >>> breakdown('df39-330-spam-51.bar')
    [('a', 'df'), ('0', '39'), ('a', '-'), ('0', '330'), ('a', '-spam-'), ('0', '51'), ('a', '.bar')]
    >>> 
    """
    fields = []
    while (s):
        if numfield.match(s):
            fields.append(('0', numfield.match(s).groups()[0]))
        else:
            fields.append(('a', othfield.match(s).groups()[0]))
        s = s[len(fields[-1][1]):]
    return fields

def compare_lines(l1, l2):
    """
    Compare two lines, returning '!=', '==', '+1', '-1', indicating
    different, same, incremented by one, or decremented by one:
    
    >>> compare_lines('my_line2439_3349.png', 'my_line2439_3350.png')
    '+1'
    >>> compare_lines('my_line2439_3349.png', 'my_line2439_3348.png')
    '-1'
    >>> compare_lines('my_line2439_3349.png', 'my_line2439_8304.png')
    '!='
    >>> compare_lines('my_line2439_3349.png', 'spam_8304.png')
    '!='
    >>> compare_lines('my_line2439_3349.png', 'my_line2439_3349.png')
    '=='
    >>> 
    """
    zl = zip(breakdown(l1), breakdown(l2))
    if all(f1==f2 for (f1,f2) in zl):
        return '=='
    
    # Check for ONE field incrementing or decrementing by 1:
    comparison = [compare_fields(f1,f2) for (f1,f2) in zl]
    if len([c for c in comparison if c=='+1']) == 1:
        return '+1'
    if len([c for c in comparison if c=='-1']) == 1:
        return '-1'
        
    #Otherwise, it doesn't match at all
    return '!='
         

def compare_fields(f1, f2):
    """
    Compare fields for equality ('=='), incremented by 1 ('+1'), decremented by 1 ('-1'),
    or other inequality ('!='):
    
    >>> compare_fields(('0','00345'), ('0','00346'))
    '+1'
    >>> 
    """
    if f1 == f2:
        return '=='
    if f1[0] == '0' and f2[0] == '0': 
        delta = int(f2[1]) - int(f1[1])
        if   delta == -1:
            return '-1'
        elif delta ==  1:
            return '+1'
    return '!='

if __name__=='__main__':
    print(main(sys.stdin))
    