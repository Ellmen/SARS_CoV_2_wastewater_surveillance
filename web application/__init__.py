# -*- coding: utf-8 -*-
import os
import time
import hashlib
import random
import shutil
import time

from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_uploads import UploadSet, configure_uploads, FASTAS, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from flask_mail import Mail, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import smtplib
import email.mime.text
import email.mime.multipart

app = Flask(__name__, template_folder='templates', static_folder='static')
# app = Flask(__name__, template_folder='../templates', static_folder='../static')
# set the uploaded file to application's path
uploaded_path = '/var/www/FlaskApp/FlaskApp'

# uploaded_path = os.getcwd()
# set up the path for uploading files
app.config['SECRET_KEY'] = 'Waste Water Surveillance'
app.config['UPLOADED_FASTAS_DEST'] = os.path.join(uploaded_path, 'uploaded_file')
# app.config['UPLOADED_FASTAS_DEST'] = os.getcwd() + '/uploaded_file'
app.config['UPLOADED_FASTAS_URL'] = os.path.join(uploaded_path, 'uploaded_file')
# app.config['UPLOADED_FASTAS_URL'] = os.getcwd() + '/uploaded_file'

# set up the file format(.fasta .fastq .txt .fa)
app.config['UPLOADED_FASTAS_ALLOW'] = set(['fas'])

# email address settings
app.config.update(dict(
    DEBUG=True,
    MAIL_SERVER="smtp.163.com",
    # MAIL_PORT=587,
    # MAIL_USE_TLS=True,
    MAIL_PORT=465,  # 163--465
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME="sars_cov2@163.com",   # my email address
    MAIL_PASSWORD="BZIXVTMTZUDTGVWL",          # this is the authorization code for the host
    MAIL_DEFAULT_SENDER=("sars_cov2@163.com"),  # defult sending address
    MAIL_DEBUG=True,
))

# create a mail application
# mail = Mail(app)   

# set up the file format(.fasta .fastq .txt .fa)
fastas = UploadSet('fastas', FASTAS)
configure_uploads(app, fastas)
# set the base directory for uploaded files
base_dir = os.path.join(uploaded_path, 'uploaded_file')
# base_dir = os.getcwd() + '/uploaded_file'
user_dir = ''
cmd = ''
paired_reads = ''
email = ''

# test if the files are in allowed format
def file_validators(filename:str)->bool:
    try:
        return filename.split('.')[-1] in ['txt','fasta','fastaq','fa']
    except:
        return False

# class UploadForm(FlaskForm):
#     fasta = FileField(validators=[FileAllowed(fastas, u'fastas/txts/fastqs Only!'), FileRequired(u'Choose a file!')])
#     submit = SubmitField(u'Upload')

# the function for sending emails
def send_email(user_dir,email):
    # show the current user directory
	print(user_dir)

	# show the files in the directory
	output_list = os.listdir(user_dir)
	print(output_list)

	attachments = []
	# get all the files to send
	if 'mismerror.txt' in output_list:
		error_file = os.path.join(user_dir,'mismerror.txt')
		attachments.append(error_file)
		if 'mismatch.txt' in output_list:
			mismatch_file = os.path.join(user_dir,'mismatch.txt')
			attachments.append(mismatch_file)
		content = 'No strains were retained. Please try increasing the coverage.'		
	else:
		if 'mismUnidentifiable_Strains_mismatch.txt' in output_list:
			unidentifiable_file = os.path.join(user_dir,'mismUnidentifiable_Strains_mismatch.txt')
			attachments.append(unidentifiable_file)
		if 'mismem_output_mismatch.csv' in output_list:
			csv_file = os.path.join(user_dir,'mismem_output_mismatch.csv')
			attachments.append(csv_file)
		if 'mismproportion_plot_mismatch.pdf' in output_list:
			pdf_file = os.path.join(user_dir,'mismproportion_plot_mismatch.pdf')
			attachments.append(pdf_file)
		content = "Here're your results:" # this is where you may edit the body of the email
					
	# recipients = [email]
	recipients = email
	subject = 'SARS_COV2_Waste_Water_Surveillance_Result' # this is where you may change the subject of the email
	body = content

	print(attachments)
	msg = MIMEMultipart()
	smtpHost = 'smtp.163.com'
	sendAddr = 'sars_cov2@163.com'
	password = 'YTKPXXRKISOTASSV'
	msg['from'] = app.config['MAIL_USERNAME']
	msg['to'] = recipients
	msg['Subject'] = subject
	txt = MIMEText(content, 'plain', 'utf-8')
	msg.attach(txt)
	for file in attachments:  # Add the attachment(output files)
		filename = file
		part = MIMEApplication(open(filename, 'rb').read())
		part.add_header('Content-Disposition', 'attachment', filename=filename)
		msg.attach(part)
	server = smtplib.SMTP(smtpHost, 25)
    # server.set_debuglevel(1)  # can be used to check bugs
	server.login(sendAddr, password)
	server.sendmail(sendAddr, recipients, str(msg))
	   # print("\n"+ str(len(filelist)) + "files are successfully sent!")
	server.quit()


def run__(request,email, frequency, paired_reads, EM_error, coverage,success=False,error=None):
    global cmd
    global user_dir
    files_list = request.files.getlist('fasta')
        # for filename in request.files.getlist('fasta'):
        # when the user upload two files and chooses yes
    if paired_reads == 'yes':
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')
            # rename the two files the user uploaded
        if file_validators(file1.filename) and file_validators(file2.filename):
            success = True
            forward_name = "forward_" + file1.filename
            print(forward_name)
            fastas.save(file1, name=forward_name)
            reverse_name = "reverse_" + file2.filename
            fastas.save(file2, name=reverse_name)

                # copy the two files to the user's directory
            forward_dir = os.path.join(base_dir, forward_name)
            reverse_dir = os.path.join(base_dir, reverse_name)
            shutil.copy(forward_dir, user_dir)
            shutil.copy(reverse_dir, user_dir)

                # set the forward and reverse path for cmd
            forward_cmd = os.path.join(user_dir, forward_name)
            reverse_cmd = os.path.join(user_dir, reverse_name)

            alignment_path = os.path.join(user_dir, 'alignment.sam')
                # define the path for mismatch.txt
            mismatch_path = os.path.join(user_dir, 'mismatch.txt')
                # turn to the index page before run the command
            cmd = "/home/software/eliminate_strains/./eliminate_strains -i /home/database/msa_0730_filtered.fasta.gz " + \
                      "-v /home/database/msa_0730_variants.txt " + \
                      "-e " + EM_error + " " + \
                      "-f " + frequency + " " + \
                      "-o " + mismatch_path + " " \
                                              "-s " + alignment_path + " " \
                                                                       "-d /home/lenore/wuhCor1 -p -1 " + forward_cmd + ' ' \
                                                                                                                        "-2 " + reverse_cmd + " -c " + coverage
            print(cmd)
        else:
        	error='Please choose two files(fasta;fastq;fa;txt only)!'


        # when the user upload only one file and chooses no
    elif paired_reads == 'no':
        file = request.files.get('file')
        if file_validators(file.filename):
            success = True
                #file.save(file.filename) if file else None
                #filename = files_list[0]
            filename = file.filename
            fastas.save(file, name=filename)
            file_dir = os.path.join(base_dir, filename)
            shutil.copy(file_dir, user_dir)
                # define the path for alignment.sam
            alignment_path = os.path.join(user_dir, 'alignment.sam')
                # define the path for mismatch.txt
            mismatch_path = os.path.join(user_dir, 'mismatch.txt')
                # turn to the index page before run the command

            file_cmd = os.path.join(user_dir, filename)
            cmd = "/home/software/eliminate_strains/./eliminate_strains -i /home/database/msa_0730_filtered.fasta.gz " + \
                      "-v /home/database/msa_0730_variants.txt " + \
                      "-e " + EM_error + " " + \
                      "-f " + frequency + " " + \
                      "-o " + mismatch_path + " " \
                                              "-s " + alignment_path + " " \
                                                                       "-d /home/lenore/wuhCor1 -0 " + file_cmd + " -c " + coverage
            print(cmd)
        else:
        	error='Please choose a file(fasta;fastq;fa;txt only)!'
    return success,error

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global user_dir
    global cmd
    global email
    global paired_reads
    success=False
    error=None
    if request.method == 'POST':
        paired_reads=request.form.get('paired_reads')
        email = request.form['email']
        if request.form['frequency']:
            frequency = request.form['frequency']
        else:
            frequency = '0.01'
        if request.form['EM_error']:
            EM_error = request.form['EM_error']
        else:
            EM_error = '0.005'
        if request.form['coverage']:
            coverage = request.form['coverage']
        else:
            coverage = '2'
        print(email, frequency, paired_reads, EM_error, coverage)  # get all the needed info

        # set the number of files
        count = random.randint(100000, 1000000)
        # set the user's own file name, e.g. guxiaoyi1809@163.com_1111111
        user_file = email + '_' + str(count)
        # set the file directory for a user
        user_dir = os.path.join(os.path.join(uploaded_path, 'uploaded_file'), user_file)
        # user_dir = os.path.join(os.getcwd() + '/uploaded_file', user_file)
        # if the directory doesn't exist, create one
        if os.path.exists(user_dir):
            user_file = email + '_' + str(count + 1)
            user_dir = os.path.join(os.path.join(uploaded_path, 'uploaded_file'), user_file)
            # user_dir = os.path.join(os.getcwd() + '/uploaded_file', user_file)
            os.mkdir(user_dir)
        else:
            os.mkdir(user_dir)
        success,error=run__(request,email, frequency, paired_reads, EM_error, coverage)
        if not success:
            return render_template('index.html', success=success, error=error)
        elif success:
            return redirect(url_for('submit_file'))

    return render_template('index.html', success=success, error=error)


@app.route('/submit', methods=['GET', 'POST'])
def submit_file():
    print(cmd)
    return render_template('submit.html', cmd=cmd)


@app.route('/back', methods=['GET', 'POST'])
def back_file():
    # os.system(cmd)
    import threading
    thread = threading.Thread(target=run_command,args=(cmd,))
    thread.start()
    #run_command(cmd)
    return render_template('submit.html', cmd=cmd)


def run_command(cmd):
    ready = False
    global user_dir
    global email
    os.system(cmd)
    # set a start time

    start = time.time()
    # this is the directory of mismatch.txt
    mismatch = os.path.join(user_dir,'mismatch.txt')
    mismerror = os.path.join(user_dir,'mismerror.txt')
    # with open(mismatch,mode='w') as f:
    #     f.write('1')
    # with open(mismerror,mode='w') as f:
    #     f.write('1')
    # judge if the mismatch.txt is not none
    while not ready:
        if os.path.exists(mismatch):
            send_email(user_dir,email)
            print('email done')
            ready = True
        else:
            # print('no mismatch')
            end = time.time()
            # if the code runs 2 hours without any output, then quit
            if end-start > 7200:
                ready = True
            else:
                pass
        time.sleep(300)
    end = time.time()
    print('It took '+ str(end-start) + ' seconds')

    print('email done')
    print(1 + 1)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
