pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5000'
        GITHUB_CREDENTIALS = credentials('github-credentials')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Backend') {
            steps {
                dir('backend') {
                    sh 'mvn -B clean package'
                }
            }
            post {
                success {
                    junit 'backend/target/surefire-reports/**/*.xml'
                }
            }
        }
        
        stage('Build Browser Extension') {
            steps {
                dir('browser-extension') {
                    sh 'npm ci'
                    sh 'npm run build'
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'browser-extension/dist/**/*', fingerprint: true
                }
            }
        }
        
        stage('Build RAG Engine') {
            steps {
                dir('rag-engine') {
                    sh 'mkdir -p build && cd build && cmake .. && make'
                }
            }
        }
        
        stage('Install AI Agent Dependencies') {
            steps {
                dir('ai-agent') {
                    sh 'pip install -r requirements.txt'
                }
            }
        }
        
        stage('Run Tests') {
            parallel {
                stage('Backend Tests') {
                    steps {
                        dir('backend') {
                            sh 'mvn test'
                        }
                    }
                }
                
                stage('Extension Tests') {
                    steps {
                        dir('browser-extension') {
                            sh 'npm test'
                        }
                    }
                }
                
                stage('RAG Engine Tests') {
                    steps {
                        dir('rag-engine/build') {
                            sh 'make test'
                        }
                    }
                }
                
                stage('AI Agent Tests') {
                    steps {
                        dir('ai-agent') {
                            sh 'python -m pytest'
                        }
                    }
                }
            }
        }
        
        stage('Build Docker Images') {
            steps {
                sh 'docker-compose build'
            }
        }
        
        stage('Push Docker Images') {
            when {
                branch 'main'
            }
            steps {
                sh 'docker-compose push'
            }
        }
        
        stage('Deploy to Local') {
            when {
                branch 'main'
            }
            steps {
                sh './deploy.sh ${BUILD_NUMBER}'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            // Send failure notification via email or Slack
            // mail to: 'team@example.com', subject: 'Build failed', body: 'The build failed. Check Jenkins for details.'
        }
    }
}
