import os
file_list=['0/','1/','2/','3/']
file_output=['1.txt','2.txt','3.txt','4.txt']
for i in range(4):
    f_out=open(file_output[i],'w')
    file_id=1
    while True:
        file_name=file_list[i]+'0'*(5-len(str(file_id)))+str(file_id)+'.txt'
        if os.path.exists(file_name):
            f_open=open(file_name,'r')
            lines=f_open.readlines()
            for line in lines:
                buf=line.split(' ')
                x_left=buf[2].strip()
                x_top=buf[3].strip()
                width=buf[4].strip()
                height=buf[5].strip()
                buf_out=[]
                buf_out.append(str(file_id))
                buf_out.append(str(-1))
                buf_out.append(str(x_left))
                buf_out.append(str(x_top))
                buf_out.append(str(width))
                buf_out.append(str(height))
                buf_out.append(str(1))
                str_out=','.join(buf_out)
                print(str_out,file=f_out)
            f_open.close()
        else:
            break
        file_id+=1
    f_out.close()